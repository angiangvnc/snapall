#!/usr/bin/env python3
"""
Tạo file SnapAll.shortcut hoàn chỉnh cho iPhone và ký số hợp lệ bằng công cụ shortcuts trên macOS.
Học hỏi và nâng cấp từ kiến trúc chuyên nghiệp của Snap Video:
1. Nhận link thông minh 3 lớp: Nút Chia sẻ (Share Sheet) -> Bảng nhớ tạm (Clipboard) -> Hộp thoại dán link (nếu cả 2 đều trống).
2. Menu lựa chọn đa năng: Chọn Tải Video HD không logo hoặc Trích xuất Âm thanh MP3.
3. Tự động lưu theo định dạng: Video lưu vào Cuộn Camera (Album Ảnh), Nhạc lưu vào ứng dụng Tệp (Files).
4. Ép kiểu chuẩn WFURLContentItem trên mọi khối Get Contents of URL, triệt tiêu 100% các lỗi URL của Apple.
Phiên bản: 5.0 (Pro Edition)
"""

import plistlib
import os
import uuid
import subprocess

def uid():
    return str(uuid.uuid4()).upper()

def create_snapall_shortcut():
    u_link_share = uid()
    u_clip = uid()
    u_link_clip = uid()
    u_combined_urls = uid()
    u_all_urls = uid()
    u_first_url = uid()

    grp_check_url = uid()
    u_ask_input = uid()
    u_ask_urls = uid()
    u_ask_first_url = uid()
    u_final_url_if = uid()

    u_api_res = uid()
    u_menu_title = uid()
    u_labels = uid()
    u_medias = uid()
    u_chosen_item = uid()
    u_download_url = uid()
    u_media_file = uid()

    grp_save_type = uid()

    prefix = 'https://snapall.vercel.app/api/parse?url='
    api_string = prefix + '\ufffc'
    api_offset_key = f'{{{len(prefix)}, 1}}'

    actions = [
        # 0. Ghi chú thông tin phím tắt
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.comment',
            'WFWorkflowActionParameters': {
                'WFCommentActionText': (
                    "⚡️ SnapAll Pro v5.0 (Kế thừa tinh hoa Snap Video)\n"
                    "• Tự động nhận link từ Nút Chia sẻ (Share Sheet) TikTok, Facebook.\n"
                    "• Tự động lấy link từ Bảng nhớ tạm, hoặc hiện ô dán link nếu chưa có.\n"
                    "• Menu chuyên nghiệp: Chọn Tải Video HD hoặc Trích xuất Âm thanh MP3.\n"
                    "• Tự động phân loại: Video vào Cuộn Camera, Âm thanh vào Tệp!"
                )
            }
        },
        # 1. Trích xuất URL từ Nút Chia sẻ (Share Sheet)
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
        # 2. Lấy nội dung từ Bảng nhớ tạm (Clipboard)
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.getclipboard',
            'WFWorkflowActionParameters': {
                'UUID': u_clip
            }
        },
        # 3. Trích xuất URL từ Bảng nhớ tạm
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
        # 4. Ghép các link tìm thấy (Ưu tiên link Chia sẻ, tiếp đến Clipboard)
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
        # 5. Phân giải danh sách URL hợp lệ
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
        # 6. Chọn link đầu tiên
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
        # 7. Kiểm tra nếu đã có URL:
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
        # 8. Nếu có rồi -> Giữ nguyên URL đó
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.detect.link',
            'WFWorkflowActionParameters': {
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
        # 9. Ngược lại (Nếu không có link từ Chia sẻ hay Clipboard -> Hiện hộp thoại dán link)
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
            'WFWorkflowActionParameters': {
                'GroupingIdentifier': grp_check_url,
                'WFControlFlowMode': 1
            }
        },
        # 10. Hộp thoại nhập link (Tự động điền Clipboard nếu có)
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.ask',
            'WFWorkflowActionParameters': {
                'UUID': u_ask_input,
                'WFAskActionPrompt': '⚡️ SnapAll: Vui lòng dán link video TikTok hoặc Facebook:',
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
        # 11. Bóc tách link từ ô người dùng nhập
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
        # 12. Lấy link đầu tiên từ ô nhập
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.getitemfromlist',
            'WFWorkflowActionParameters': {
                'UUID': u_ask_first_url,
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
        # 13. Kết thúc điều kiện chọn link
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
            'WFWorkflowActionParameters': {
                'UUID': u_final_url_if,
                'GroupingIdentifier': grp_check_url,
                'WFControlFlowMode': 2
            }
        },
        # 14. Gọi API SnapAll lấy dữ liệu bóc tách
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
                                'WFValue': {'Value': {'string': 'SnapAll/5.0 iOS'}, 'WFSerializationType': 'WFTextTokenString'}
                            }
                        ]
                    },
                    'WFSerializationType': 'WFDictionaryFieldValue'
                },
                'WFURL': {
                    'Value': {
                        'attachmentsByRange': {
                            api_offset_key: {
                                'OutputUUID': u_final_url_if,
                                'OutputName': 'If Result',
                                'Type': 'ActionOutput',
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
        # 15. Lấy tiêu đề hiển thị (menu_title)
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
        # 16. Lấy danh sách lựa chọn (labels)
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
        # 17. Lấy từ điển link media (medias)
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
        # 18. Hiển thị Menu lựa chọn chuyên nghiệp cho người dùng
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
        # 19. Lấy link download tương ứng mục người dùng đã chọn
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
        # 20. Tải file media (Video hoặc Audio)
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
        # 21. Kiểm tra nếu mục chọn chứa 🎵 (Audio)
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
        # 22. Lưu vào ứng dụng Tệp (Files / iCloud Drive)
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
        # 23. Báo thành công âm thanh
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.notification',
            'WFWorkflowActionParameters': {
                'WFNotificationActionTitle': '🎵 SnapAll Audio',
                'WFNotificationActionBody': 'Đã trích xuất & lưu file âm thanh vào Tệp!'
            }
        },
        # 24. Ngược lại (Nếu chọn Video)
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
            'WFWorkflowActionParameters': {
                'GroupingIdentifier': grp_save_type,
                'WFControlFlowMode': 1
            }
        },
        # 25. Lưu video vào Thư viện Ảnh (Album Cuộn Camera)
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
        # 26. Báo thành công video
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.notification',
            'WFWorkflowActionParameters': {
                'WFNotificationActionTitle': '⚡️ SnapAll Video',
                'WFNotificationActionBody': '✅ Đã tải và lưu video vào Cuộn Camera!'
            }
        },
        # 27. Kết thúc điều kiện phân loại lưu
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
        'WFWorkflowClientRelease': '5.0',
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

    subprocess.run(['shortcuts', 'sign', '--mode', 'anyone', '--input', source_path, '--output', output_path], check=True)
    print(f"✅ Đã tạo và ký thành công {output_path} ({os.path.getsize(output_path)} bytes)")

if __name__ == '__main__':
    create_snapall_shortcut()
