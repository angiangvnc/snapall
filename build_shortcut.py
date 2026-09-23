#!/usr/bin/env python3
"""
Tạo file SnapAll.shortcut hoàn chỉnh cho iPhone và ký số hợp lệ bằng công cụ shortcuts trên macOS.
"""

import plistlib
import os
import uuid
import subprocess

def uid():
    return str(uuid.uuid4()).upper()

def create_snapall_shortcut():
    u_link = uid()
    u_api_url = uid()
    u_req = uid()
    u_data = uid()
    u_play = uid()
    u_music = uid()
    u_video = uid()
    u_audio = uid()
    u_menu_grp = uid()

    actions = [
        # 1. Ghi chú
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.comment',
            'WFWorkflowActionParameters': {
                'WFCommentActionText': (
                    "⚡️ SnapAll Downloader v2.0\n"
                    "• Tải video TikTok KHÔNG logo / watermark ➔ Lưu vào Thư viện Ảnh.\n"
                    "• Trích xuất âm thanh (Audio MP3) ➔ Lưu vào Tệp / Chia sẻ.\n"
                    "• Hoạt động qua nút Chia sẻ (Share Sheet) trong app TikTok."
                )
            }
        },
        # 2. Lấy link từ Bảng chia sẻ
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.detect.link',
            'WFWorkflowActionParameters': {
                'UUID': u_link,
                'WFInput': {
                    'Value': {
                        'Type': 'ExtensionInput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },
        # 3. Tạo URL gọi TikWM API
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.gettext',
            'WFWorkflowActionParameters': {
                'UUID': u_api_url,
                'WFTextActionText': {
                    'Value': {
                        'attachmentsByRange': {
                            '{31, 1}': {
                                'OutputUUID': u_link,
                                'Type': 'ActionOutput'
                            }
                        },
                        'string': 'https://www.tikwm.com/api/?url=\ufffc'
                    },
                    'WFSerializationType': 'WFTextTokenString'
                }
            }
        },
        # 4. Tải JSON từ TikWM API
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.downloadurl',
            'WFWorkflowActionParameters': {
                'UUID': u_req,
                'WFURL': {
                    'Value': {
                        'OutputUUID': u_api_url,
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },
        # 5. Lấy trường data
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
            'WFWorkflowActionParameters': {
                'UUID': u_data,
                'WFDictionaryKey': 'data',
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_req,
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },
        # 6. Menu Start (WFControlFlowMode: 0)
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.choosefrommenu',
            'WFWorkflowActionParameters': {
                'GroupingIdentifier': u_menu_grp,
                'WFControlFlowMode': 0,
                'WFMenuPrompt': '⚡️ SnapAll: Bạn muốn tải gì?',
                'WFMenuItems': [
                    '🎬 Tải Video HD (Không Logo)',
                    '🎵 Trích Xuất Âm Thanh (MP3)'
                ]
            }
        },
        # 7. Menu Item 1: Video (WFControlFlowMode: 1)
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.choosefrommenu',
            'WFWorkflowActionParameters': {
                'GroupingIdentifier': u_menu_grp,
                'WFControlFlowMode': 1,
                'WFMenuItemTitle': '🎬 Tải Video HD (Không Logo)'
            }
        },
        # 8. Lấy khóa play
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
            'WFWorkflowActionParameters': {
                'UUID': u_play,
                'WFDictionaryKey': 'play',
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_data,
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
                'UUID': u_video,
                'WFURL': {
                    'Value': {
                        'OutputUUID': u_play,
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },
        # 10. Lưu vào Album ảnh (Cuộn Camera)
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.savetocameraroll',
            'WFWorkflowActionParameters': {
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_video,
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },
        # 11. Menu Item 2: Audio (WFControlFlowMode: 1)
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.choosefrommenu',
            'WFWorkflowActionParameters': {
                'GroupingIdentifier': u_menu_grp,
                'WFControlFlowMode': 1,
                'WFMenuItemTitle': '🎵 Trích Xuất Âm Thanh (MP3)'
            }
        },
        # 12. Lấy khóa music
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
            'WFWorkflowActionParameters': {
                'UUID': u_music,
                'WFDictionaryKey': 'music',
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_data,
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },
        # 13. Tải file audio MP3
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.downloadurl',
            'WFWorkflowActionParameters': {
                'UUID': u_audio,
                'WFURL': {
                    'Value': {
                        'OutputUUID': u_music,
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },
        # 14. Bảng chia sẻ (Lưu vào Tệp / Gửi ứng dụng)
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.sharesheet',
            'WFWorkflowActionParameters': {
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_audio,
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },
        # 15. Menu End (WFControlFlowMode: 2)
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.choosefrommenu',
            'WFWorkflowActionParameters': {
                'GroupingIdentifier': u_menu_grp,
                'WFControlFlowMode': 2
            }
        },
        # 16. Thông báo hoàn thành
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.notification',
            'WFWorkflowActionParameters': {
                'WFNotificationActionTitle': '⚡️ SnapAll',
                'WFNotificationActionBody': '✅ Đã tải và lưu thành công!'
            }
        }
    ]

    shortcut_dict = {
        'WFWorkflowMinimumClientVersion': 900,
        'WFWorkflowClientVersion': '2607.1',
        'WFWorkflowClientRelease': '3.0',
        'WFWorkflowIcon': {
            'WFWorkflowIconStartColor': 4282601983, # Xanh dương / Gradient
            'WFWorkflowIconGlyphNumber': 59511      # Tia chớp / Tải xuống
        },
        'WFWorkflowTypes': [
            'NCWidget',
            'ActionExtension' # Hiện trong bảng chia sẻ (Share Sheet)
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

    # Ký số bằng lệnh của macOS
    cmd = ['shortcuts', 'sign', '--mode', 'anyone', '--input', source_path, '--output', output_path]
    subprocess.run(cmd, check=True)
    print(f"✅ Đã tạo và ký thành công {output_path} ({os.path.getsize(output_path)} bytes)")

if __name__ == '__main__':
    create_snapall_shortcut()
