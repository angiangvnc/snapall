#!/usr/bin/env python3
"""
Tạo file SnapAll.shortcut hoàn chỉnh cho iPhone và ký số hợp lệ bằng công cụ shortcuts trên macOS.
Hỗ trợ cả 2 cách dùng:
1. Bấm nút Chia sẻ (Share Sheet) trong TikTok / Facebook -> Tự động nhận link.
2. Bấm 'Sao chép liên kết' (Copy link) rồi chạy phím tắt từ Widget / Màn hình chính.
Phiên bản: 4.0 (Fix hoàn toàn lỗi nhận diện URL từ TikTok / Facebook Share Sheet)
"""

import plistlib
import os
import uuid
import subprocess

def uid():
    return str(uuid.uuid4()).upper()

def create_snapall_shortcut():
    # UUIDs
    u_link_share = uid()
    u_clip = uid()
    u_link_clip = uid()
    u_combined_urls = uid()
    u_all_urls = uid()
    u_url = uid()

    g_url = uid()
    u_api_url = uid()
    u_api_res = uid()
    u_vid_url = uid()

    g_vid = uid()
    u_vid_file = uid()

    actions = [
        # 0. Ghi chú thông tin phiên bản
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.comment',
            'WFWorkflowActionParameters': {
                'WFCommentActionText': (
                    "⚡️ SnapAll v4.0 Downloader\n"
                    "• Tự động bóc tách link từ Nút Chia sẻ (Share Sheet) TikTok, Facebook.\n"
                    "• Tự động lấy link từ Bảng nhớ tạm nếu mở phím tắt trực tiếp.\n"
                    "• Tải video TikTok KHÔNG logo / watermark.\n"
                    "• Tải video Facebook HD/SD.\n"
                    "• Tự động lưu thẳng video vào Album Ảnh (Cuộn Camera)!"
                )
            }
        },
        # 1. Trích xuất link trực tiếp từ Đầu vào phím tắt (Share Sheet)
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
        # 4. Gộp 2 nguồn link (Ưu tiên link từ Chia sẻ lên đầu, tiếp đến là Clipboard)
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
        # 5. Phân giải danh sách link sạch
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
        # 6. Lấy link đầu tiên tìm thấy
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
        # 7. Kiểm tra: NẾU có link hợp lệ
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
            'WFWorkflowActionParameters': {
                'GroupingIdentifier': g_url,
                'WFCondition': 100,  # Has Any Value
                'WFControlFlowMode': 0,  # If
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_url,
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },
        # 8. Tạo URL gọi API Serverless
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
        # 9. Gửi request đến API phân giải video
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
        # 10. Trích xuất link video từ kết quả JSON
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
        # 11. Kiểm tra: NẾU API trả về link video hợp lệ
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
            'WFWorkflowActionParameters': {
                'GroupingIdentifier': g_vid,
                'WFCondition': 100,  # Has Any Value
                'WFControlFlowMode': 0,  # If
                'WFInput': {
                    'Value': {
                        'OutputUUID': u_vid_url,
                        'Type': 'ActionOutput'
                    },
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        },
        # 12. Tải file video MP4 chất lượng cao
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
        # 13. Tự động lưu video vào Album Cuộn Camera
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
        # 14. Thông báo hoàn tất
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.notification',
            'WFWorkflowActionParameters': {
                'WFNotificationActionTitle': '⚡️ SnapAll',
                'WFNotificationActionBody': '✅ Đã tải và lưu video vào Cuộn Camera!'
            }
        },
        # 15. NẾU KHÔNG có video hợp lệ từ API (Else g_vid)
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
            'WFWorkflowActionParameters': {
                'GroupingIdentifier': g_vid,
                'WFControlFlowMode': 1  # Otherwise
            }
        },
        # 16. Cảnh báo lỗi phân giải video
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.alert',
            'WFWorkflowActionParameters': {
                'WFAlertActionTitle': '⚡️ SnapAll',
                'WFAlertActionMessage': '⚠️ Không tìm thấy video hợp lệ từ liên kết này hoặc video ở chế độ riêng tư. Vui lòng kiểm tra lại!',
                'WFAlertActionCancelButtonShown': False
            }
        },
        # 17. Kết thúc điều kiện video (End If g_vid)
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
            'WFWorkflowActionParameters': {
                'GroupingIdentifier': g_vid,
                'WFControlFlowMode': 2  # End If
            }
        },
        # 18. NẾU KHÔNG tìm thấy link nào từ cả Chia sẻ lẫn Clipboard (Else g_url)
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
            'WFWorkflowActionParameters': {
                'GroupingIdentifier': g_url,
                'WFControlFlowMode': 1  # Otherwise
            }
        },
        # 19. Cảnh báo chưa có link
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.alert',
            'WFWorkflowActionParameters': {
                'WFAlertActionTitle': '⚡️ SnapAll',
                'WFAlertActionMessage': '⚠️ Không tìm thấy liên kết video!\n\nVui lòng mở TikTok hoặc Facebook, bấm nút Chia sẻ (Share) -> chọn SnapAll, hoặc Sao chép liên kết trước khi chạy phím tắt.',
                'WFAlertActionCancelButtonShown': False
            }
        },
        # 20. Kết thúc điều kiện URL (End If g_url)
        {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
            'WFWorkflowActionParameters': {
                'GroupingIdentifier': g_url,
                'WFControlFlowMode': 2  # End If
            }
        }
    ]

    # Đăng ký ĐẦY ĐỦ tất cả các loại dữ liệu đầu vào để iOS KHÔNG BAO GIỜ lọc bỏ hoặc làm rỗng link khi Chia sẻ từ TikTok, Facebook, Safari, Instagram...
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
        'WFWorkflowClientRelease': '4.0',
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
