#!/usr/bin/env python3
"""
    SPDX-FileCopyrightText: 2023 Jonas Tobias Hopusch <git@jotoho.de>
    SPDX-License-Identifier: AGPL-3.0-only
"""
from collections import OrderedDict
from pathlib import Path
from sys import stderr
from tempfile import TemporaryDirectory
from typing import Callable, Literal, TypedDict, NotRequired, Required

from code.mod import mod_change_activation, ModConfig, ValidModSettings, mod_exists, \
    process_mod_subdir_argument, get_mod_last_update_check
from code.creation import create_mod_space, recursive_lower_case_rename, ask_for_path, \
    transfer_mod_files, extract_archive
from code.deployer import deploy_filesystem, stop_filesystem, are_paths_on_same_filesystem, \
    is_fuse_overlayfs_mounted
from code.mod import get_mod_ids, get_mod_versions, select_latest_version, validate_mod_id, \
    mod_at_version_limit, write_mod_priority, read_mod_priority, build_mod_order, \
    parse_mod_conflicts, version_exists, parse_version_tag
from code.settings import InstanceSettings, ValidInstanceSettings, get_instance_settings
from code.tools import current_date


class SubcommandArgDict(TypedDict, total=False):
    """
    type information for cli argument information that may be passed to subcommands of modfs
    """
    show_args: Required[bool]
    mod_id: Required[str]
    instance: Required[Path]
    version_string: NotRequired[str]
    subcommand: NotRequired[str]
    listtype: NotRequired[Literal["mods", "conflicts", "versions", "priority", "updatecheck"]]
    all: NotRequired[bool]
    preserve_source: NotRequired[bool]
    subdir: NotRequired[str]
    import_path: NotRequired[Path]
    set_author: NotRequired[str]
    set_name: NotRequired[str]
    set_link: NotRequired[str]
    repairaction: NotRequired[str]
    modids: NotRequired[list[str]]
    gamefiles: NotRequired[bool]
    overflow: NotRequired[bool]
    reorder_operation: NotRequired[Literal["before", "after", "highest", "lowest"]]
    mod_to_reorder: NotRequired[str]
    reference_modid: NotRequired[str]
    developer_action: NotRequired[str]
    config_actions: NotRequired[Literal["get", "set", "unset", "list"]]
    setting_id: NotRequired[str]
    setting_val: NotRequired[str]
    version: NotRequired[str]
    mod_action: NotRequired[Literal["set", "info"]]
    attribute: NotRequired[Literal["author", "name", "note", "link"]]
    value: NotRequired[str]
    exclude_today: NotRequired[bool]


def subcommand_list(args: SubcommandArgDict) -> None:
    """

    :param args:
    :type args:
    """
    if args["listtype"] == "mods":
        print("List of installed mods:")
        for mod in get_mod_ids(args["instance"]):
            print(mod)
    elif args["listtype"] == "versions":
        if not args["all"] and len(args["modids"]) == 0:
            print("You need to specify mods or give the --all flag to list versions.",
                  file=stderr)
            exit(1)
        mods_to_process = list(args["modids"]) + get_mod_ids() if args["all"] else args["modids"]
        for mod in sorted(set(mods_to_process)):
            isDisabled = not ModConfig(mod).get(ValidModSettings.ENABLED)
            print(f"{mod}:" + (" (disabled)" if isDisabled else ""))
            versions = get_mod_versions(mod)
            for date, subversions in sorted(versions.items()):
                first_subversion = True
                for subver in sorted(subversions):
                    pri_ver_str = date
                    if first_subversion:
                        first_subversion = False
                    else:
                        pri_ver_str = (' ' * len(date))
                    ver_str = "  " + pri_ver_str + '/' + subver
                    tags: set[str] = set()
                    is_latest = (date, subver) == select_latest_version(mod)
                    if is_latest:
                        tags.add("latest")
                    active_version = ModConfig(mod).get(ValidModSettings.MOD_VERSION)
                    is_selected_ver = ((date, subver) == parse_version_tag(active_version)
                                      if active_version != "latest"
                                      else is_latest)
                    if is_selected_ver:
                        tags.add("selected")
                    print(ver_str, *tags)
    elif args["listtype"] == "priority":
        for mod_id in read_mod_priority().keys():
            print(mod_id)
    elif args["listtype"] == "conflicts":
        for mods, files in parse_mod_conflicts().items():
            print(set(mods))
            for file in files:
                print((" " * 4) + str(file))
    elif args["listtype"] == "updatecheck":
        mod_list: set[str] = set(args["modids"])
        if args["all"]:
            mod_list |= set(get_mod_ids())
        if len(mod_list) <= 0:
            print("You must select one or more mods to list.", file=stderr)
            exit(1)
        print("The selected mods were last checked for updates on the following dates:")
        listdata: dict[str | None, set[str]] = {}
        exclude_disabled = args["exclude_today"]
        for mod in mod_list:
            if exclude_disabled and not ModConfig(mod, args["instance"]).get(ValidModSettings.ENABLED):
                continue
            date = get_mod_last_update_check(mod)
            if date not in listdata:
                listdata[date] = set()
            listdata[date].add(mod)

        if args["exclude_today"]:
            today = current_date()
            if today in listdata:
                del listdata[today]

        for date in sorted(listdata.keys(), key=lambda s: s if s is not None else ""):
            mods = listdata[date]
            print((date + ":") if date is not None else "Never:")
            for mod in sorted(mods):
                print((12 * " ") + mod)


def subcommand_activate(args: SubcommandArgDict) -> None:
    """

    :param args:
    :type args:
    """
    deployment_directory: Path | None = InstanceSettings(args["instance"]).get(
        ValidInstanceSettings.DEPLOYMENT_TARGET_DIR)
    if deployment_directory is None:
        from sys import stderr
        print("""
        No deployment directory has been configured for this instance. Aborting deployment.
        """.strip(), file=stderr)
        exit(1)
    if not deployment_directory.is_absolute():
        deployment_directory = (args["instance"] / deployment_directory).resolve()
    mods_to_deploy: OrderedDict[str, tuple[str, str]] = OrderedDict()
    for mod in read_mod_priority().keys():
        if not ModConfig(mod, args["instance"]).get(ValidModSettings.ENABLED):
            continue
        version_conf: str = ModConfig(mod).get(ValidModSettings.MOD_VERSION)
        if version_conf.lower() == "latest":
            version_to_use = select_latest_version(mod)
        else:
            version_to_use = parse_version_tag(version_conf)
        if version_to_use is None:
            continue
        mods_to_deploy[mod] = version_to_use
    deploy_filesystem(deployment_directory, mods_to_deploy)


def subcommand_deactivate(args: SubcommandArgDict) -> None:
    """

    :param args:
    :type args:
    """
    deployment_directory = InstanceSettings(args["instance"]).get(
        ValidInstanceSettings.DEPLOYMENT_TARGET_DIR)
    if deployment_directory is None:
        from sys import stderr
        print("""
            No deployment directory has been configured for this instance. Cannot deactivate.
        """.strip(), file=stderr)
        exit(1)
    else:
        stop_filesystem(deployment_directory)


def subcommand_import(args: SubcommandArgDict) -> None:
    """

    :param args:
    :type args:
    """
    only_copy: bool = args["preserve_source"]
    mod_id: str = args["mod_id"]
    if not validate_mod_id(mod_id):
        print("A mod id may only contain lower case letters a-z, digits 0-9 and the minus sign",
              file=stderr)
        exit(1)

    if mod_at_version_limit(mod_id, current_date(), args["instance"]):
        print("A mod may only have 100 subversions per day (00-99). Aborting import.",
              file=stderr)
        stderr.flush()
        exit(1)
    else:
        print(f"Importing mod {mod_id}")

    source: Path = args["import_path"].resolve(strict=True)
    raw_destination = create_mod_space(mod_id).resolve()
    processed_subdir = process_mod_subdir_argument(args["subdir"],
                                                   mod_id=mod_id,
                                                   src_dir=source)
    destination: Path = (raw_destination / processed_subdir).resolve()
    if not destination.is_relative_to(raw_destination):
        print("Subdirectories must not break out of the assigned mod folder!",
              file=stderr)
        exit(1)
    destination.mkdir(parents=True, exist_ok=True)

    if source.is_dir():
        transfer_mod_files(source, destination, only_copy)
    elif source.is_file():
        with TemporaryDirectory() as tmpdir_str:
            tmpdir = Path(tmpdir_str)
            extract_archive(source, tmpdir)
            if len(set(tmpdir.iterdir())) == 0:
                raise "Extraction of archive failed. No files in extraction destination."
            source_subdirs: list[Path] = list(filter(lambda p: p.is_dir(),
                                                     tmpdir.rglob(f"**/{args['subdir']}")))
            if len(source_subdirs) == 0:
                transfer_mod_files(tmpdir, destination, only_copy=False)
            elif len(source_subdirs) == 1:
                transfer_mod_files(source_subdirs[0], destination, only_copy=False)
            else:
                raise ("Multiple candidates for source within archive. You must prepare these "
                       "files manually.")
    else:
        print("internal logic error: source is neither file nor directory", file=stderr)
        exit(1)
    recursive_lower_case_rename(raw_destination)

    cfg = ModConfig(mod_id)
    cfg.set(ValidModSettings.LAST_UPDATE_CHECK, current_date())
    author: str | None = args["set_author"]
    if author is not None:
        cfg.set(ValidModSettings.AUTHOR, author)
    name: str | None = args["set_name"]
    if name is not None:
        cfg.set(ValidModSettings.PRETTY_NAME, name)
    link: str | None = args["set_link"]
    if link is not None:
        cfg.set(ValidModSettings.HYPERLINK, link)


def subcommand_repair(args: SubcommandArgDict) -> None:
    """

    :param args:
    :type args:
    """
    if args["repairaction"] == "filenamecase":
        from code.mod import resolve_base_dir
        all_mods: bool = args["all"]
        named_mods: list[str] = args["modids"]
        rename_game_files: bool = args["gamefiles"]
        rename_overflow: bool = args["overflow"]
        mods_to_rename: set[str] = set(named_mods + (get_mod_ids() if all_mods else []))
        for mod in mods_to_rename:
            mod_dir = resolve_base_dir() / 'mods' / mod
            recursive_lower_case_rename(mod_dir)
        if rename_game_files:
            recursive_lower_case_rename(
                get_instance_settings().get(ValidInstanceSettings.DEPLOYMENT_TARGET_DIR)
            )
        if rename_overflow:
            overflow_dir = get_instance_settings().get(
                ValidInstanceSettings.FILESYSTEM_OVERFLOW_DIR
            )
            assert isinstance(overflow_dir, Path)
            if overflow_dir.is_dir():
                recursive_lower_case_rename(overflow_dir)
    elif args["repairaction"] == "filepriority":
        write_mod_priority(read_mod_priority())
    else:
        print("Unknown repair action", file=stderr)
        exit(1)


def subcommand_init(args: SubcommandArgDict) -> None:
    """

    :param args:
    :type args:
    """
    get_instance_settings().initialize_settings_directory()
    (args["instance"] / 'mods').mkdir(exist_ok=True, parents=True)
    write_mod_priority(read_mod_priority(base_dir=args["instance"]), base_dir=args["instance"])

    target_directory = ask_for_path(
        "Please specify the directory to deploy the mods of this instance to",
        lambda path: path.is_dir())

    overflow_directory = ask_for_path(
        "Please specify an overflow directory for modified files",
        lambda path: path.is_dir())

    work_directory = ask_for_path(
        "Please specify a working directory on the same filesystem as the target directory",
        lambda path: path.is_dir() and are_paths_on_same_filesystem(path, target_directory))

    settings = get_instance_settings()
    settings.set(ValidInstanceSettings.DEPLOYMENT_TARGET_DIR, target_directory)
    settings.set(ValidInstanceSettings.FILESYSTEM_OVERFLOW_DIR, overflow_directory)
    settings.set(ValidInstanceSettings.FILESYSTEM_WORK_DIR, work_directory)

    recursive_lower_case_rename(target_directory)


def subcommand_reorder(args: SubcommandArgDict) -> None:
    """

    :param args:
    :type args:
    """
    if is_fuse_overlayfs_mounted():
        print("You cannot reorder mods while the filesystem is active!",
              file=stderr)
        exit(1)

    type_operation = Literal["before", "after", "highest", "lowest"]
    reorder_operation: type_operation | None = args["reorder_operation"]
    mod_id_to_reorder: str = args["mod_to_reorder"]
    if reorder_operation in {"after", "before"}:
        reference_modid: str | None = args["reference_modid"]
        if reference_modid is None:
            print("No reference for reordering specified.",
                  file=stderr)
            exit(1)

        mod_order = list(read_mod_priority().keys())

        if mod_id_to_reorder not in mod_order:
            print("mod to reorder does not exist",
                  file=stderr)
            exit(1)
        elif reference_modid not in mod_order:
            print("reference mod does not exist",
                  file=stderr)
            exit(1)

        if reorder_operation == "after":
            mod_order.remove(mod_id_to_reorder)
            index = mod_order.index(reference_modid)
            mod_order = mod_order[:index + 1] + [mod_id_to_reorder] + mod_order[index + 1:]
        elif reorder_operation == "before":
            mod_order.remove(mod_id_to_reorder)
            index = mod_order.index(reference_modid)
            mod_order = mod_order[:index] + [mod_id_to_reorder] + mod_order[index:]

        write_mod_priority(build_mod_order(mod_order))
    elif reorder_operation in {"highest", "lowest"}:
        mod_order = read_mod_priority()
        if reorder_operation == "highest":
            if mod_id_to_reorder in mod_order.keys():
                mod_order.move_to_end(mod_id_to_reorder)
            else:
                print(f"Mod {mod_id_to_reorder} does not exist.",
                      file=stderr)
        elif reorder_operation == "lowest":
            if mod_id_to_reorder in mod_order.keys():
                mod_order.move_to_end(mod_id_to_reorder, last=False)
            else:
                print(f"Mod {mod_id_to_reorder} does not exist.",
                      file=stderr)
        write_mod_priority(mod_order)
    else:
        print("reorder operation has not been specified. See --help for more info.",
              file=stderr)
        exit(1)


def subcommand_developer(args: SubcommandArgDict) -> None:
    """

    :param args:
    :type args:
    :return:
    :rtype:
    """
    no_dev_warning: bool = get_instance_settings().get(
        ValidInstanceSettings.SUPPRESS_DEVELOPER_CMD_WARNING)
    if not no_dev_warning:
        print("""
YOU ARE EXECUTING A DEVELOPER SUBCOMMAND.
These features are exclusively meant for debugging and may cease working at any time
or even cause permanent damage.
Do not use them unless you know what you're doing or are following instructions by a developer.
    """.strip())

    action: str | None = args["developer_action"]
    if action is None:
        print("developer subcommand is missing. see --help for details", file=stderr)
    elif action == "create-blank-mod":
        print("Created directory:", create_mod_space(args["mod_id"]))


def subcommand_status(_: SubcommandArgDict) -> None:
    """

    :param _:
    :type _:
    """
    target_dir_setting = ValidInstanceSettings.DEPLOYMENT_TARGET_DIR
    assert target_dir_setting.value_type == Path
    target_dir: Path | None = get_instance_settings().get(target_dir_setting)

    if target_dir is None:
        print("target directory is unknown")
    elif is_fuse_overlayfs_mounted(target_dir):
        print("filesystem is active on path " + str(target_dir))
    else:
        print("filesystem is not active")


def subcommand_config(args: SubcommandArgDict) -> None:
    """

    :param args:
    :type args:
    """
    operation: Literal["get", "set", "unset", "list"] | None = args["config_actions"]

    match operation:
        case "list":
            for cfg in ValidInstanceSettings:
                cfg_id = cfg.setting_id
                if get_instance_settings().is_set(cfg):
                    print("CUSTOM: ", cfg_id)
                else:
                    print("DEFAULT:", cfg_id)
        case _ if operation in {"get", "set", "unset"}:
            setting_id: str = args["setting_id"].lower()
            matching_settings = list(filter(
                lambda cfg2: cfg2.setting_id.lower().startswith(setting_id.lower()),
                ValidInstanceSettings))

            if len(matching_settings) < 1:
                print("setting not found", file=stderr)
                exit(1)
            elif len(matching_settings) > 1:
                print("multiple matching settings", file=stderr)
                exit(1)

            setting: ValidInstanceSettings = matching_settings[0]

            match operation:
                case "get":
                    if setting_id.lower() != setting.setting_id.lower():
                        print("warning: querying config via incomplete id may not work when using "
                              "different versions of modfs", file=stderr)
                    print(setting.setting_id, "=",
                          get_instance_settings().get(setting, force_retrieval=True))
                case "set":
                    if setting_id.lower() != setting.setting_id.lower():
                        print("warning: setting config via incomplete id may not work when using "
                              "different versions of modfs", file=stderr)
                    new_value_str: str = args["setting_val"]
                    new_value = setting.value_type(new_value_str)
                    get_instance_settings().set(setting, new_value)
                case "unset":
                    if setting_id.lower() != setting.setting_id.lower():
                        print("warning: unsetting config via incomplete id may not work when using "
                              "different versions of modfs", file=stderr)
                    get_instance_settings().unset(setting)
        case _:
            print("Invalid config operation", file=stderr)
            exit(1)


def subcommand_delete(args: SubcommandArgDict) -> None:
    """

    :param args:
    :type args:
    """
    mod_id: str = args["mod_id"]
    mod_dir: Path = args["instance"] / 'mods' / mod_id
    if mod_dir.is_dir():
        from shutil import rmtree
        rmtree(mod_dir)
    mod_conf: Path = args["instance"] / 'mods' / f"{mod_id}.json"
    mod_conf.unlink(missing_ok=True)


def subcommand_enable(args: SubcommandArgDict) -> None:
    """

    :param args:
    :type args:
    """
    mod_change_activation(args["mod_id"], True, base_dir=args["instance"])


def subcommand_disable(args: SubcommandArgDict) -> None:
    """

    :param args:
    :type args:
    """
    mod_change_activation(args["mod_id"], False, base_dir=args["instance"])


def subcommand_useversion(args: SubcommandArgDict) -> None:
    """

    :param args:
    :type args:
    """
    mod_id: str = args["mod_id"]
    version_str: str = args["version"]

    try:
        if version_str == "latest":
            ModConfig(mod_id).set(ValidModSettings.MOD_VERSION, "latest")
        else:
            version_date, version_subversion = parse_version_tag(version_str)

            if version_exists(mod_id, version_date, version_subversion):
                ModConfig(mod_id).set(ValidModSettings.MOD_VERSION,
                                      f"{version_date}/{version_subversion}")
            else:
                print(f"Version {version_str} does not exist!", file=stderr)
                exit(1)
    except ValueError as e:
        print(e, file=stderr)
        exit(1)


def subcommand_mod(args: SubcommandArgDict) -> None:
    """

    :param args:
    :type args:
    """
    mod_id: str = args["mod_id"]
    action: Literal["set", "info"] | None = args["mod_action"]
    if action is None:
        print("You must specify an action to take with the given mod",
              file=stderr)
        exit(1)

    cfg = ModConfig(mod_id)
    if action == "set":
        attribute: Literal["author", "name", "note", "link"] = args["attribute"]
        value: str = args["value"]
        if attribute == "author":
            cfg.set(ValidModSettings.AUTHOR, value)
        elif attribute == "name":
            cfg.set(ValidModSettings.PRETTY_NAME, value)
        elif attribute == "note":
            cfg.set(ValidModSettings.NOTES, value)
        elif attribute == "link":
            cfg.set(ValidModSettings.HYPERLINK, value)
        else:
            print("mod attribute not recognized. no modifications were made.")
            exit(1)
    elif action == "info":
        print(f"Retrieving data on {mod_id}...")
        cfg_name: str = cfg.get(ValidModSettings.PRETTY_NAME)
        print(f"Name:\t{cfg_name if len(cfg_name) > 0 else mod_id}")
        cfg_author: str = cfg.get(ValidModSettings.AUTHOR)
        print(f"Author:\t{cfg_author if len(cfg_author) > 0 else 'unknown'}")
        cfg_link: str = cfg.get(ValidModSettings.HYPERLINK)
        if len(cfg_link) > 0:
            print(f"Link:\t{cfg_link}")
        print(f"Status:\t" + "Enabled" if cfg.get(ValidModSettings.ENABLED) else "Disabled")
        latest_version = select_latest_version(mod_id)
        if latest_version is not None:
            latest_date, latest_sub = latest_version
            print(f"Latest version: {latest_date}/{latest_sub}")
            cfg_version = cfg.get(ValidModSettings.MOD_VERSION)
            if cfg_version.lower() == "latest":
                print(f"Active version: {latest_date}/{latest_sub}")
            else:
                active_date, active_sub = parse_version_tag(cfg_version)
                print(f"Active version: {active_date}/{active_sub}")
            last_updated = get_mod_last_update_check(mod_id)
            print("Last checked for updates on: "
                  f"{last_updated if last_updated is not None else 'Never'}")
        cfg_notes: str = cfg.get(ValidModSettings.NOTES)
        if len(cfg_notes) > 0:
            from textwrap import indent
            print("User notes:")
            print(indent(cfg_notes, " " * 2))


def subcommand_version(args: SubcommandArgDict) -> None:
    """

    :param args:
    :type args:
    """
    version_string: str = args["version_string"]
    if version_string is None or len(version_string) < 1:
        version_string = "unknown"
    print("modfs version", version_string)


def subcommand_markuptodate(args: SubcommandArgDict) -> None:
    """

    :param args:
    :type args:
    """
    for mod in args["modids"]:
        ModConfig(mod).set(ValidModSettings.LAST_UPDATE_CHECK, current_date())


def get_subcommands_table() -> dict[str, Callable[[SubcommandArgDict], None]]:
    """

    :return:
    :rtype:
    """
    return {
        "list": subcommand_list,
        "activate": subcommand_activate,
        "on": subcommand_activate,
        "deactivate": subcommand_deactivate,
        "off": subcommand_deactivate,
        "status": subcommand_status,
        "import": subcommand_import,
        "repair": subcommand_repair,
        "init": subcommand_init,
        "reorder": subcommand_reorder,
        "developer": subcommand_developer,
        "config": subcommand_config,
        "delete": subcommand_delete,
        "enable": subcommand_enable,
        "disable": subcommand_disable,
        "useversion": subcommand_useversion,
        "mod": subcommand_mod,
        "version": subcommand_version,
        "markuptodate": subcommand_markuptodate,
    }
