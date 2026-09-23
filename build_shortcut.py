#!/usr/bin/env python3
"""
Tạo file SnapAll.shortcut hoàn chỉnh cho iPhone và ký số hợp lệ bằng công cụ shortcuts trên macOS.
Hỗ trợ cả 2 cách dùng:
1. Bấm nút Chia sẻ (Share Sheet) trong TikTok / Facebook -> Tự động nhận link.
2. Bấm 'Sao chép liên kết' (Copy link) rồi chạy phím tắt từ Widget / Màn hình chính.
Phiên bản: 4.1 (Clean Linear Flow - Không lỗi tham số 'choose a value for each parameter')
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
    u_url = uid()
    u_api_url = uid()
    u_api_res = uid()
    u_vid_url = uid()
    u_vid_file = uid()

    actions = [
        # 0. Ghi chú thông tin
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.comment',
            'WFWorkflowActionParameters': {
                'WFCommentActionText': (
                    "⚡️ SnapAll Downloader v4.1\n"
                    "• Tự động bóc tách link từ Nút Chia sẻ (Share Sheet) TikTok, Facebook.\n"
                    "• Tự động lấy link từ Bảng nhớ tạm nếu mở phím tắt trực tiếp.\n"
                    "• Tải video TikTok KHÔNG logo / watermark.\n"
                    "• Tải video Facebook HD/SD.\n"
                    "• Tự động lưu thẳng video vào Album Ảnh (Cuộn Camera)!"
                )
            }
        },
        # 1. Trích xuất link từ Đầu vào phím tắt (Share Sheet)
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.detect.link',
            'WFWorkflowActionParameters': {
                'UUID': u_link_share,
                'WFInput': {
                    'Value': {
                        'Type': 'ExtensionInput'
                    },
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
        # 3. Trích xuất link từ Bảng nhớ tạm
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.detect.link',
            'WFWorkflowActionParameters': {
                'UUID': u_link_clip,
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_clip,
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },
        # 4. Gộp các link tìm thấy (Ưu tiên link Chia sẻ lên đầu, tiếp đến Clipboard)
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.gettext',
            'WFWorkflowActionParameters': {
                'UUID': u_combined_urls,
                'WFTextActionText': {
                    'Value': {
                        'attachmentsByRange': {
                            '{0, 1}': {
                                'OutputUUID': u_link_share,
                                'Type': 'ActionOutput'
                            },
                            '{2, 1}': {
                                'OutputUUID': u_link_clip,
                                'Type': 'ActionOutput'
                            }
                        },
                        'string': '\ufffc\n\ufffc'
                    },
                    'WFSerializationType': 'WFTextTokenString'
                }
            }
        },
        # 5. Phân giải danh sách URL chuẩn
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.detect.link',
            'WFWorkflowActionParameters': {
                'UUID': u_all_urls,
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_combined_urls,
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },
        # 6. Chọn URL đầu tiên
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.getitemfromlist',
            'WFWorkflowActionParameters': {
                'UUID': u_url,
                'WFItemSpecifier': 'First Item',
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_all_urls,
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },
        # 7. Ghép URL vào API Serverless
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.gettext',
            'WFWorkflowActionParameters': {
                'UUID': u_api_url,
                'WFTextActionText': {
                    'Value': {
                        'attachmentsByRange': {
                            '{38, 1}': {
                                'OutputUUID': u_url,
                                'Type': 'ActionOutput'
                            }
                        },
                        'string': 'https://snapall.vercel.app/api/parse?url=\ufffc'
                    },
                    'WFSerializationType': 'WFTextTokenString'
                }
            }
        },
        # 8. Gọi API lấy dữ liệu JSON
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.downloadurl',
            'WFWorkflowActionParameters': {
                'UUID': u_api_res,
                'WFURL': {
                    'Value': {
                        'OutputUUID': u_api_url,
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },
        # 9. Bóc tách link video sạch logo
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
            'WFWorkflowActionParameters': {
                'UUID': u_vid_url,
                'WFDictionaryKey': 'video',
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_api_res,
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },
        # 10. Tải file video MP4
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.downloadurl',
            'WFWorkflowActionParameters': {
                'UUID': u_vid_file,
                'WFURL': {
                    'Value': {
                        'OutputUUID': u_vid_url,
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },
        # 11. Lưu video vào Thư viện Ảnh (Album Cuộn Camera)
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.savetocameraroll',
            'WFWorkflowActionParameters': {
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_vid_file,
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },
        # 12. Bắn thông báo hoàn tất
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.notification',
            'WFWorkflowActionParameters': {
                'WFNotificationActionTitle': '⚡️ SnapAll',
                'WFNotificationActionBody': '✅ Đã tải và lưu video vào Cuộn Camera!'
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
        'WFWorkflowClientRelease': '4.1',
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
