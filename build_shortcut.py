#!/usr/bin/env python3
"""
Tạo file SnapAll.shortcut hoàn chỉnh cho iPhone và ký số hợp lệ bằng công cụ shortcuts trên macOS.
Kiến trúc v6.0 - Fix lỗi URL: dùng Set Variable thay cho If Result.
1. Nhận link thông minh 3 lớp: Nút Chia sẻ (Share Sheet) -> Bảng nhớ tạm (Clipboard) -> Hộp thoại dán link.
2. Dùng Set Variable để lưu URL cuối cùng - tránh lỗi "If Result" không hợp lệ.
3. Menu lựa chọn đa năng: Tải Video HD hoặc Trích xuất Âm thanh MP3.
4. Tự động lưu: Video -> Cuộn Camera, Âm thanh -> Tệp.
Phiên bản: 6.0 (URL Fix Edition)
"""

import plistlib
import os
import uuid
import subprocess

def uid():
    return str(uuid.uuid4()).upper()

def create_snapall_shortcut():
    # UUID cho từng action
    u_link_share    = uid()
    u_clip          = uid()
    u_link_clip     = uid()
    u_combined_urls = uid()
    u_all_urls      = uid()
    u_first_url     = uid()

    grp_check_url   = uid()
    u_ask_input     = uid()
    u_ask_urls      = uid()
    u_ask_first     = uid()

    # Tên biến lưu URL cuối cùng (Named Variable)
    var_final_url   = 'final_url'

    u_api_res       = uid()
    u_menu_title    = uid()
    u_labels        = uid()
    u_medias        = uid()
    u_chosen_item   = uid()
    u_download_url  = uid()
    u_media_file    = uid()

    grp_save_type   = uid()

    prefix          = 'https://snapall.vercel.app/api/parse?url='
    api_string      = prefix + '\ufffc'
    api_offset_key  = f'{{{len(prefix)}, 1}}'

    actions = [
        # 0. Comment
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.comment',
            'WFWorkflowActionParameters': {
                'WFCommentActionText': (
                    "⚡️ SnapAll Pro v6.0\n"
                    "• Nhận link từ Share Sheet, Clipboard, hoặc hộp thoại.\n"
                    "• Gọi API snapall.vercel.app để bóc tách link video.\n"
                    "• Menu chọn: Tải Video HD hoặc Trích xuất Audio MP3.\n"
                    "• Tự động lưu: Video → Cuộn Camera, Audio → Tệp."
                )
            }
        },

        # 1. Detect URL từ Share Sheet
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.detect.link',
            'WFWorkflowActionParameters': {
                'UUID': u_link_share,
                'WFInput': {
                    'Value': {'Type': 'ExtensionInput'},
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },

        # 2. Lấy Clipboard
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.getclipboard',
            'WFWorkflowActionParameters': {
                'UUID': u_clip
            }
        },

        # 3. Detect URL từ Clipboard
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.detect.link',
            'WFWorkflowActionParameters': {
                'UUID': u_link_clip,
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_clip,
                        'OutputName': 'Clipboard',
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },

        # 4. Ghép text
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.gettext',
            'WFWorkflowActionParameters': {
                'UUID': u_combined_urls,
                'WFTextActionText': {
                    'Value': {
                        'attachmentsByRange': {
                            '{0, 1}': {
                                'OutputUUID': u_link_share,
                                'OutputName': 'URLs',
                                'Type': 'ActionOutput'
                            },
                            '{2, 1}': {
                                'OutputUUID': u_link_clip,
                                'OutputName': 'URLs',
                                'Type': 'ActionOutput'
                            }
                        },
                        'string': '\ufffc\n\ufffc'
                    },
                    'WFSerializationType': 'WFTextTokenString'
                }
            }
        },

        # 5. Detect URL từ text ghép
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.detect.link',
            'WFWorkflowActionParameters': {
                'UUID': u_all_urls,
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_combined_urls,
                        'OutputName': 'Text',
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },

        # 6. Lấy link đầu tiên
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.getitemfromlist',
            'WFWorkflowActionParameters': {
                'UUID': u_first_url,
                'WFItemSpecifier': 'First Item',
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_all_urls,
                        'OutputName': 'URLs',
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },

        # 7. IF: Item from List has any value?
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
            'WFWorkflowActionParameters': {
                'GroupingIdentifier': grp_check_url,
                'WFControlFlowMode': 0,
                'WFCondition': 100,
                'WFInput': {
                    'Type': 'Variable',
                    'Variable': {
                        'Value': {
                            'OutputUUID': u_first_url,
                            'OutputName': 'Item from List',
                            'Type': 'ActionOutput'
                        },
                        'WFSerializationType': 'WFTextTokenAttachment'
                    }
                }
            }
        },

        # 8. (TRUE) Set Variable final_url = Item from List
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
            'WFWorkflowActionParameters': {
                'WFVariableName': var_final_url,
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_first_url,
                        'OutputName': 'Item from List',
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },

        # 9. ELSE
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
            'WFWorkflowActionParameters': {
                'GroupingIdentifier': grp_check_url,
                'WFControlFlowMode': 1
            }
        },

        # 10. Hộp thoại nhập link
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.ask',
            'WFWorkflowActionParameters': {
                'UUID': u_ask_input,
                'WFAskActionPrompt': '⚡️ SnapAll: Dán link video TikTok hoặc Facebook:',
                'WFAskActionDefaultAnswer': {
                    'Value': {
                        'string': '\ufffc',
                        'attachmentsByRange': {
                            '{0, 1}': {'Type': 'Clipboard'}
                        }
                    },
                    'WFSerializationType': 'WFTextTokenString'
                },
                'WFAllowsMultilineText': False
            }
        },

        # 11. Detect URL từ input người dùng
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.detect.link',
            'WFWorkflowActionParameters': {
                'UUID': u_ask_urls,
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_ask_input,
                        'OutputName': 'Provided Input',
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },

        # 12. Lấy link đầu tiên từ input người dùng
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.getitemfromlist',
            'WFWorkflowActionParameters': {
                'UUID': u_ask_first,
                'WFItemSpecifier': 'First Item',
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_ask_urls,
                        'OutputName': 'URLs',
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },

        # 13. (ELSE) Set Variable final_url = link người dùng nhập
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
            'WFWorkflowActionParameters': {
                'WFVariableName': var_final_url,
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_ask_first,
                        'OutputName': 'Item from List',
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },

        # 14. END IF
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
            'WFWorkflowActionParameters': {
                'GroupingIdentifier': grp_check_url,
                'WFControlFlowMode': 2
            }
        },

        # 15. Gọi API SnapAll - dùng Named Variable final_url
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.downloadurl',
            'WFWorkflowActionParameters': {
                'UUID': u_api_res,
                'CustomOutputName': 'api_data',
                'WFHTTPHeaders': {
                    'Value': {
                        'WFDictionaryFieldValueItems': [
                            {
                                'WFKey': {'Value': {'string': 'User-Agent'}, 'WFSerializationType': 'WFTextTokenString'},
                                'WFItemType': 0,
                                'WFValue': {'Value': {'string': 'SnapAll/6.0 iOS'}, 'WFSerializationType': 'WFTextTokenString'}
                            }
                        ]
                    },
                    'WFSerializationType': 'WFDictionaryFieldValue'
                },
                'WFURL': {
                    'Value': {
                        'attachmentsByRange': {
                            api_offset_key: {
                                'Type': 'Variable',
                                'VariableName': var_final_url,
                                'Aggrandizements': [
                                    {
                                        'Type': 'WFCoercionVariableAggrandizement',
                                        'CoercionItemClass': 'WFURLContentItem'
                                    }
                                ]
                            }
                        },
                        'string': api_string
                    },
                    'WFSerializationType': 'WFTextTokenString'
                }
            }
        },

        # 16. Lấy menu_title
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
            'WFWorkflowActionParameters': {
                'UUID': u_menu_title,
                'CustomOutputName': 'menu_title',
                'WFDictionaryKey': 'menu_title',
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_api_res,
                        'OutputName': 'api_data',
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },

        # 17. Lấy labels
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
            'WFWorkflowActionParameters': {
                'UUID': u_labels,
                'CustomOutputName': 'labels',
                'WFDictionaryKey': 'labels',
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_api_res,
                        'OutputName': 'api_data',
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },

        # 18. Lấy medias
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
            'WFWorkflowActionParameters': {
                'UUID': u_medias,
                'CustomOutputName': 'medias',
                'WFDictionaryKey': 'medias',
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_api_res,
                        'OutputName': 'api_data',
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },

        # 19. Menu lựa chọn
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.choosefromlist',
            'WFWorkflowActionParameters': {
                'UUID': u_chosen_item,
                'CustomOutputName': 'Chosen Item',
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_labels,
                        'OutputName': 'labels',
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                },
                'WFChooseFromListActionPrompt': {
                    'Value': {
                        'attachmentsByRange': {
                            '{0, 1}': {
                                'OutputUUID': u_menu_title,
                                'OutputName': 'menu_title',
                                'Type': 'ActionOutput'
                            }
                        },
                        'string': '\ufffc'
                    },
                    'WFSerializationType': 'WFTextTokenString'
                },
                'WFChooseFromListActionSelectMultiple': False
            }
        },

        # 20. Lấy download URL
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
            'WFWorkflowActionParameters': {
                'UUID': u_download_url,
                'CustomOutputName': 'download_url',
                'WFDictionaryKey': {
                    'Value': {
                        'attachmentsByRange': {
                            '{0, 1}': {
                                'OutputUUID': u_chosen_item,
                                'OutputName': 'Chosen Item',
                                'Type': 'ActionOutput'
                            }
                        },
                        'string': '\ufffc'
                    },
                    'WFSerializationType': 'WFTextTokenString'
                },
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_medias,
                        'OutputName': 'medias',
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },

        # 21. Tải file media
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.downloadurl',
            'WFWorkflowActionParameters': {
                'UUID': u_media_file,
                'CustomOutputName': 'Downloaded File',
                'WFURL': {
                    'Value': {
                        'attachmentsByRange': {
                            '{0, 1}': {
                                'OutputUUID': u_download_url,
                                'OutputName': 'download_url',
                                'Type': 'ActionOutput',
                                'Aggrandizements': [
                                    {
                                        'Type': 'WFCoercionVariableAggrandizement',
                                        'CoercionItemClass': 'WFURLContentItem'
                                    }
                                ]
                            }
                        },
                        'string': '\ufffc'
                    },
                    'WFSerializationType': 'WFTextTokenString'
                }
            }
        },

        # 22. IF: chứa 🎵?
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
            'WFWorkflowActionParameters': {
                'GroupingIdentifier': grp_save_type,
                'WFControlFlowMode': 0,
                'WFCondition': 99,
                'WFConditionalActionString': '🎵',
                'WFInput': {
                    'Type': 'Variable',
                    'Variable': {
                        'Value': {
                            'OutputUUID': u_chosen_item,
                            'OutputName': 'Chosen Item',
                            'Type': 'ActionOutput'
                        },
                        'WFSerializationType': 'WFTextTokenAttachment'
                    }
                }
            }
        },

        # 23. Lưu Audio vào Tệp
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.documentpicker.save',
            'WFWorkflowActionParameters': {
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_media_file,
                        'OutputName': 'Downloaded File',
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                },
                'WFAskWhereToSave': True
            }
        },

        # 24. Thông báo Audio
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.notification',
            'WFWorkflowActionParameters': {
                'WFNotificationActionTitle': '🎵 SnapAll Audio',
                'WFNotificationActionBody': 'Đã trích xuất & lưu file âm thanh vào Tệp!'
            }
        },

        # 25. ELSE (Video)
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
            'WFWorkflowActionParameters': {
                'GroupingIdentifier': grp_save_type,
                'WFControlFlowMode': 1
            }
        },

        # 26. Lưu Video vào Cuộn Camera
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.savetocameraroll',
            'WFWorkflowActionParameters': {
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_media_file,
                        'OutputName': 'Downloaded File',
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },

        # 27. Thông báo Video
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.notification',
            'WFWorkflowActionParameters': {
                'WFNotificationActionTitle': '⚡️ SnapAll Video',
                'WFNotificationActionBody': '✅ Đã tải và lưu video vào Cuộn Camera!'
            }
        },

        # 28. END IF save type
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
            'WFWorkflowActionParameters': {
                'GroupingIdentifier': grp_save_type,
                'WFControlFlowMode': 2
            }
        }
    ]

    all_content_classes = [
        'WFAppStoreAppContentItem',
        'WFArticleContentItem',
        'WFContactContentItem',
        'WFDateContentItem',
        'WFEmailAddressContentItem',
        'WFGenericFileContentItem',
        'WFImageContentItem',
        'WFiTunesProductContentItem',
        'WFLocationContentItem',
        'WFDCMapsLinkContentItem',
        'WFAVAssetContentItem',
        'WFPDFContentItem',
        'WFPhoneNumberContentItem',
        'WFRichTextContentItem',
        'WFSafariWebPageContentItem',
        'WFStringContentItem',
        'WFURLContentItem'
    ]

    shortcut_dict = {
        'WFWorkflowMinimumClientVersion': 900,
        'WFWorkflowClientVersion': '2607.1',
        'WFWorkflowClientRelease': '6.0',
        'WFWorkflowIcon': {
            'WFWorkflowIconStartColor': 4282601983,
            'WFWorkflowIconGlyphNumber': 59511
        },
        'WFWorkflowTypes': [
            'NCWidget',
            'ActionExtension',
            'QuickLook'
        ],
        'WFWorkflowInputContentItemClasses': all_content_classes,
        'WFWorkflowActions': actions
    }

    source_path = 'SnapAll_Source.shortcut'
    output_path = 'SnapAll.shortcut'

    with open(source_path, 'wb') as f:
        plistlib.dump(shortcut_dict, f)

    subprocess.run(
        ['shortcuts', 'sign', '--mode', 'anyone', '--input', source_path, '--output', output_path],
        check=True
    )
    print(f"✅ Đã tạo và ký thành công {output_path} ({os.path.getsize(output_path)} bytes)")

if __name__ == '__main__':
    create_snapall_shortcut()
