#!/usr/bin/env python3
"""
Tạo file SnapAll.shortcut hoàn chỉnh cho iPhone và ký số hợp lệ bằng công cụ shortcuts trên macOS.
Hỗ trợ cả 2 cách dùng:
1. Bấm nút Chia sẻ (Share Sheet) trong TikTok / Facebook.
2. Bấm 'Sao chép liên kết' (Copy link) rồi chạy phím tắt từ Widget / Màn hình chính.
"""

import plistlib
import os
import uuid
import subprocess

def uid():
    return str(uuid.uuid4()).upper()

def create_snapall_shortcut():
    u_clip = uid()
    u_raw = uid()
    u_match = uid()
    u_url = uid()
    u_api = uid()
    u_req = uid()
    u_video_url = uid()
    u_video_file = uid()

    actions = [
        # 1. Ghi chú
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.comment',
            'WFWorkflowActionParameters': {
                'WFCommentActionText': (
                    "⚡️ SnapAll v3.0 Downloader\n"
                    "• Tự động nhận link từ Nút Chia sẻ HOẶC Bảng nhớ tạm (khi bấm Sao chép liên kết).\n"
                    "• Tải video TikTok KHÔNG logo / watermark.\n"
                    "• Tải video Facebook HD/SD.\n"
                    "• Tự động lưu video thẳng vào Thư viện Ảnh (Cuộn Camera)!"
                )
            }
        },
        # 2. Lấy nội dung từ Bảng nhớ tạm
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.getclipboard',
            'WFWorkflowActionParameters': {
                'UUID': u_clip
            }
        },
        # 3. Gộp cả Đầu vào chia sẻ và Bảng nhớ tạm
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.gettext',
            'WFWorkflowActionParameters': {
                'UUID': u_raw,
                'WFTextActionText': {
                    'Value': {
                        'attachmentsByRange': {
                            '{0, 1}': {
                                'Type': 'ExtensionInput'
                            },
                            '{2, 1}': {
                                'OutputUUID': u_clip,
                                'Type': 'ActionOutput'
                            }
                        },
                        'string': '\ufffc\n\ufffc'
                    },
                    'WFSerializationType': 'WFTextTokenString'
                }
            }
        },
        # 4. Trích xuất URL chuẩn bằng RegEx
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.text.match',
            'WFWorkflowActionParameters': {
                'UUID': u_match,
                'WFMatchTextPattern': 'https?://[a-zA-Z0-9\\.\\_\\/\\-\\?\\=\\&\\%\\#\\+]+',
                'WFMatchTextCaseSensitive': False,
                'text': {
                    'Value': {
                        'OutputUUID': u_raw,
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },
        # 5. Lấy liên kết đầu tiên
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.getitemfromlist',
            'WFWorkflowActionParameters': {
                'UUID': u_url,
                'WFItemSpecifier': 'First Item',
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_match,
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },
        # 6. Tạo đường dẫn gọi API Vercel Serverless
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.gettext',
            'WFWorkflowActionParameters': {
                'UUID': u_api,
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
        # 7. Gọi API Vercel lấy JSON
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.downloadurl',
            'WFWorkflowActionParameters': {
                'UUID': u_req,
                'WFURL': {
                    'Value': {
                        'OutputUUID': u_api,
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },
        # 8. Bóc trường video từ JSON
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
            'WFWorkflowActionParameters': {
                'UUID': u_video_url,
                'WFDictionaryKey': 'video',
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_req,
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },
        # 9. Tải file video MP4
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.downloadurl',
            'WFWorkflowActionParameters': {
                'UUID': u_video_file,
                'WFURL': {
                    'Value': {
                        'OutputUUID': u_video_url,
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },
        # 10. Lưu thẳng vào Cuộn Camera (Album ảnh)
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.savetocameraroll',
            'WFWorkflowActionParameters': {
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_video_file,
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },
        # 11. Thông báo hoàn thành
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.notification',
            'WFWorkflowActionParameters': {
                'WFNotificationActionTitle': '⚡️ SnapAll',
                'WFNotificationActionBody': '✅ Đã tải và lưu video vào Cuộn Camera!'
            }
        }
    ]

    shortcut_dict = {
        'WFWorkflowMinimumClientVersion': 900,
        'WFWorkflowClientVersion': '2607.1',
        'WFWorkflowClientRelease': '3.0',
        'WFWorkflowIcon': {
            'WFWorkflowIconStartColor': 4282601983,
            'WFWorkflowIconGlyphNumber': 59511
        },
        'WFWorkflowTypes': [
            'NCWidget',
            'ActionExtension'
        ],
        'WFWorkflowInputContentItemClasses': [
            'WFURLContentItem',
            'WFStringContentItem'
        ],
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
