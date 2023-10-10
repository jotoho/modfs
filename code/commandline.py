#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2023 Jonas Tobias Hopusch <git@jotoho.de>
# SPDX-License-Identifier: AGPL-3.0-only
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace
from os import getcwd
from pathlib import Path

from code.mod import cast_validate_mod_id
from code.settings import InstanceSettings, ValidInstanceSettings


def get_instance_path() -> Path:
    # Create a parser just for the early value
    parser = ArgumentParser(add_help=False)
    parser.add_argument("--instance",
                        type=Path,
                        default=Path(getcwd()),
                        help="The instance to run your commands on. Defaults to current working "
                             "directory.")
    args, _ = parser.parse_known_args()
    return args.instance


def process_commandline_args() -> Namespace:
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter,
                            description="""
            modfs is a tool for simple game modding needs on Linux systems.
            You can use it to store mods and deploy them via fuse-overlayfs.
        """)
    parser.add_argument("--instance",
                        type=Path,
                        default=Path(getcwd()),
                        help="The instance to run your commands on. Defaults to current working "
                             "directory.")
    parser.add_argument("--show-args",
                        action="store_true",
                        help="Prints the evaluated CLI object to stdout for debugging")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)
    init_parser = subparsers.add_parser("init",
                                        formatter_class=ArgumentDefaultsHelpFormatter,
                                        help="Initializes new instance directory")
    init_parser.add_argument("--installhelper",
                             action='store_true',
                             help="""
        Whether a runnable file should be created in the instance
        directory, which forwards commands to modfs. Currently not
        implemented.
    """)
    subparsers.add_parser("activate",
                          aliases=["on"],
                          formatter_class=ArgumentDefaultsHelpFormatter,
                          help="Deploy filesystem")
    subparsers.add_parser("deactivate",
                          aliases=["off"],
                          formatter_class=ArgumentDefaultsHelpFormatter,
                          help="Stop filesystem deployment")
    enable_parser = subparsers.add_parser("enable")
    enable_parser.add_argument("mod_id",
                               type=cast_validate_mod_id)
    disable_parser = subparsers.add_parser("disable")
    disable_parser.add_argument("mod_id",
                                type=cast_validate_mod_id)
    config_parser = subparsers.add_parser("config",
                                          formatter_class=ArgumentDefaultsHelpFormatter,
                                          help="View or modify instance configuration")
    config_subparsers = config_parser.add_subparsers(dest="config_actions", required=True)
    config_get_parser = config_subparsers.add_parser("get",
                                                     formatter_class=ArgumentDefaultsHelpFormatter,
                                                     help="View configuration value(s)")
    config_get_parser.add_argument("setting_id")
    config_set_parser = config_subparsers.add_parser("set",
                                                     formatter_class=ArgumentDefaultsHelpFormatter,
                                                     help="Change a configuration value")
    config_set_parser.add_argument("setting_id")
    config_set_parser.add_argument("setting_val")
    config_unset_parser = config_subparsers.add_parser("unset",
                                                       formatter_class=ArgumentDefaultsHelpFormatter,
                                                       help="Delete a configuration value")
    config_subparsers.add_parser("list",
                                 formatter_class=ArgumentDefaultsHelpFormatter,
                                 help="Show list of all valid setting ids")
    config_unset_parser.add_argument("setting_id")
    subparsers.add_parser("status",
                          formatter_class=ArgumentDefaultsHelpFormatter,
                          help="Show statistics and other helpful information.")
    import_parser = subparsers.add_parser("import",
                                          help="Import a foreign directory as a mod",
                                          formatter_class=ArgumentDefaultsHelpFormatter)
    import_parser.add_argument("--preserve-source",
                               action="store_true",
                               help="Copy file from source, instead of moving")
    import_parser.add_argument("--subdir",
                               type=str,
                               default=(InstanceSettings(get_instance_path()).get(
                                   ValidInstanceSettings.DEFAULT_MOD_SUBFOLDER)),
                               help="The subfolder of the new mod to install these contents into")
    import_parser.add_argument("--set-author",
                               type=str,
                               default=None)
    import_parser.add_argument("--set-name",
                               type=str,
                               default=None)
    import_parser.add_argument("--set-link",
                               type=str,
                               default=None)
    import_parser.add_argument("modid",
                               type=str)
    import_parser.add_argument("import_path",
                               type=Path,
                               help="the source directory")
    delete_parser = subparsers.add_parser("delete",
                                          formatter_class=ArgumentDefaultsHelpFormatter,
                                          help="Delete a mod or one specific version.")
    delete_parser.add_argument("mod_id",
                               type=cast_validate_mod_id)
    list_parser = subparsers.add_parser("list",
                                        formatter_class=ArgumentDefaultsHelpFormatter,
                                        help="List known resources")
    list_subparsers = list_parser.add_subparsers(dest="listtype", required=True)
    list_subparsers.add_parser("mods",
                               formatter_class=ArgumentDefaultsHelpFormatter,
                               help="List all installed mods")
    list_subparsers.add_parser("priority",
                               formatter_class=ArgumentDefaultsHelpFormatter,
                               help="List installed mods in order of increasing priority")
    list_subparsers.add_parser("conflicts",
                               formatter_class=ArgumentDefaultsHelpFormatter,
                               help="List possible conflicts between all installed mods")
    list_version_parser = list_subparsers.add_parser("versions",
                                                     formatter_class=ArgumentDefaultsHelpFormatter,
                                                     help="List the mods")
    list_version_parser.add_argument("--all",
                                     action="store_true")
    list_version_parser.add_argument("mod_id",
                                     nargs='*',
                                     default=[],
                                     type=cast_validate_mod_id)
    version_select_parser = subparsers.add_parser("useversion",
                                                  formatter_class=ArgumentDefaultsHelpFormatter,
                                                  help="Make modfs use a different version.")
    version_select_parser.add_argument("mod_id",
                                       type=cast_validate_mod_id)
    version_select_parser.add_argument("version")
    reorder_parser = subparsers.add_parser("reorder",
                                           formatter_class=ArgumentDefaultsHelpFormatter,
                                           help="Change mod priority.")
    reorder_parser.add_argument("mod_to_reorder",
                                type=cast_validate_mod_id)
    reorder_operation_parser = reorder_parser.add_subparsers(dest="reorder_operation",
                                                             help="the method by which to "
                                                                  "determine this mod's new "
                                                                  "position", required=True)
    reorder_operation_parser.add_parser("lowest")
    reorder_operation_parser.add_parser("highest")
    reorder_before = reorder_operation_parser.add_parser("before")
    reorder_after = reorder_operation_parser.add_parser("after")
    reorder_before.add_argument("reference_modid",
                                type=cast_validate_mod_id)
    reorder_after.add_argument("reference_modid",
                               type=cast_validate_mod_id)
    repair_parser = subparsers.add_parser("repair",
                                          formatter_class=ArgumentDefaultsHelpFormatter,
                                          help="A collection of repair or maintenance features")
    repair_subparser = repair_parser.add_subparsers(dest="repairaction", required=True)
    repair_subparser.add_parser("filepriority",
                                formatter_class=ArgumentDefaultsHelpFormatter)
    repair_filenamecase_parser = repair_subparser.add_parser("filenamecase",
                                                             formatter_class=ArgumentDefaultsHelpFormatter)
    repair_filenamecase_parser.add_argument("--all",
                                            action="store_true",
                                            help="""
        Process all mods
    """)
    repair_filenamecase_parser.add_argument("--gamefiles",
                                            action="store_true",
                                            help="""
        Process the game files in the target directory
    """.strip())
    repair_filenamecase_parser.add_argument("modids",
                                            nargs='*',
                                            default=[],
                                            type=cast_validate_mod_id,
                                            help="""
        List of ids of installed mods to process
    """)
    dev_parser = subparsers.add_parser("developer")
    dev_subparsers = dev_parser.add_subparsers(dest="developer_action", required=True)
    dev_blank_mod = dev_subparsers.add_parser("create-blank-mod")
    dev_blank_mod.add_argument("mod_id")
    mod_parser = subparsers.add_parser("mod")
    mod_parser.add_argument("mod_id")
    mod_action_parsers = mod_parser.add_subparsers(dest="mod_action", required=True)
    mod_set_parser = mod_action_parsers.add_parser("set")
    mod_set_parser.add_argument("attribute", choices={"author", "name", "note", "link"})
    mod_set_parser.add_argument("value")
    mod_action_parsers.add_parser("info")
    subparsers.add_parser("help",
                          formatter_class=ArgumentDefaultsHelpFormatter,
                          help="Show this help information")

    evaluated_args = parser.parse_args()
    if (not evaluated_args.subcommand) or (evaluated_args.subcommand == "help"):
        parser.print_help()
        from os import EX_OK
        exit(EX_OK)
    else:
        return evaluated_args
