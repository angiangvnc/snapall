#!/usr/bin/env python3
"""
SnapAll & Snap Video Shortcut Generator
Tạo file .shortcut chuẩn kiến trúc Apple Shortcuts theo nội dung ảnh chụp:
1. Nhận link đa nguồn (Share Sheet, Clipboard, hoặc Hỏi trực tiếp).
2. Xử lý mở link đặc biệt {{open-url}}.
3. Lặp qua các lựa chọn (Repeat Loop):
   - Regex trích xuất định dạng (mp4|mov|jpg|jpeg|heic|png|webp|mp3|m4a).
   - Đổi thành chữ thường (ext).
   - Sinh số ngẫu nhiên 1 - 9999999 (Random Number).
   - Đổi tên file chuẩn: snapvideo--[title] - [Random Number].[ext].
   - Phân loại lưu trữ: Âm thanh 🎵 -> Tệp (Documents), Video -> Ảnh (Recents).
   - Ghi nhận trạng thái m_file / m_album.
4. Menu hoàn tất (menu_done):
   - Thêm m_album, m_file, close vào menu_done.
   - Chọn từ menu_done: Mở Photos hoặc Mở Tệp trong Finder.
   - Kết thúc phím tắt (Stop this shortcut).
"""

import plistlib
import os
import uuid
import subprocess

# ==============================================================================
# 🌐 CẤU HÌNH API RIÊNG CỦA BẠN:
# Bạn có thể thay đổi endpoint này thành domain của bạn bất kỳ lúc nào:
# Ví dụ: "https://your-domain.com/api.php?url=" hoặc Vercel Serverless
# ==============================================================================
DEFAULT_API_URL = "https://snapall.vercel.app/api/parse?url="

def uid():
    return str(uuid.uuid4()).upper()

def make_attachment(output_uuid, output_name, coercion_class=None, aggrandizements=None):
    val = {
        'OutputUUID': output_uuid,
        'OutputName': output_name,
        'Type': 'ActionOutput'
    }
    if coercion_class:
        val['Aggrandizements'] = [{
            'Type': 'WFCoercionVariableAggrandizement',
            'CoercionItemClass': coercion_class
        }]
    elif aggrandizements:
        val['Aggrandizements'] = aggrandizements
    return {
        'Value': val,
        'WFSerializationType': 'WFTextTokenAttachment'
    }

def make_var_attachment(var_name):
    return {
        'Value': {
            'VariableName': var_name,
            'Type': 'Variable'
        },
        'WFSerializationType': 'WFTextTokenAttachment'
    }

def build_workflow(api_base_url="https://snapall.vercel.app/api/parse?url=", shortcut_name="Snap Video"):
    actions = []

    # UUIDs
    u_link_share = uid()
    u_clip = uid()
    u_link_clip = uid()
    u_combined_urls = uid()
    u_all_urls = uid()
    u_first_url = uid()

    grp_check_url = uid()
    u_ask_input = uid()
    u_ask_urls = uid()
    u_ask_first = uid()

    u_get_url = uid()
    grp_open_url = uid()
    u_replace_open = uid()
    grp_check_replaced = uid()
    u_open_url = uid()

    u_init_album = uid()
    u_init_file = uid()
    u_init_close = uid()

    u_api_res = uid()
    u_title = uid()
    u_labels = uid()
    u_medias = uid()
    u_menu_title = uid()

    u_chosen_item = uid()
    u_count_select = uid()

    grp_repeat = uid()
    u_item_index = uid()
    u_dl_url = uid()
    u_fetch_res = uid()

    grp_repeat_not_first = uid()
    u_match_ext = uid()
    u_ext_lower = uid()
    u_rand_num = uid()
    u_set_name = uid()

    grp_save_type = uid()
    u_save_file = uid()
    u_save_recents = uid()

    grp_loop_check = uid()
    u_menu_select = uid()
    grp_check_album = uid()
    grp_check_file = uid()

    # 0. Comment
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.comment',
        'WFWorkflowActionParameters': {
            'WFCommentActionText': (
                f"⚡️ {shortcut_name} Pro\n"
                "• Tự động nhận diện liên kết từ Share Sheet hoặc Clipboard.\n"
                "• Lọc & tải video HD hoặc trích xuất âm thanh MP3 chất lượng cao.\n"
                "• Regex trích xuất đuôi mở rộng, sinh số ngẫu nhiên & đổi tên file chuẩn.\n"
                "• Tự động lưu: Âm thanh -> Tệp, Video -> Cuộn Camera.\n"
                "• Menu điều hướng sau khi tải xong (Xem Album / Mở Tệp / Đóng)."
            )
        }
    })

    # 1. Detect link từ Share Sheet
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.detect.link',
        'WFWorkflowActionParameters': {
            'UUID': u_link_share,
            'CustomOutputName': 'URLs Share',
            'WFInput': {
                'Value': {'Type': 'ExtensionInput'},
                'WFSerializationType': 'WFTextTokenAttachment'
            }
        }
    })

    # 2. Lấy Clipboard
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getclipboard',
        'WFWorkflowActionParameters': {
            'UUID': u_clip
        }
    })

    # 3. Detect link từ Clipboard
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.detect.link',
        'WFWorkflowActionParameters': {
            'UUID': u_link_clip,
            'CustomOutputName': 'URLs Clipboard',
            'WFInput': make_attachment(u_clip, 'Clipboard')
        }
    })

    # 4. Ghép Text từ 2 nguồn
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.gettext',
        'WFWorkflowActionParameters': {
            'UUID': u_combined_urls,
            'WFTextActionText': {
                'Value': {
                    'attachmentsByRange': {
                        '{0, 1}': {'OutputUUID': u_link_share, 'OutputName': 'URLs Share', 'Type': 'ActionOutput'},
                        '{2, 1}': {'OutputUUID': u_link_clip, 'OutputName': 'URLs Clipboard', 'Type': 'ActionOutput'}
                    },
                    'string': '\ufffc\n\ufffc'
                },
                'WFSerializationType': 'WFTextTokenString'
            }
        }
    })

    # 5. Detect link từ text ghép
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.detect.link',
        'WFWorkflowActionParameters': {
            'UUID': u_all_urls,
            'WFInput': make_attachment(u_combined_urls, 'Text')
        }
    })

    # 6. Lấy link đầu tiên
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getitemfromlist',
        'WFWorkflowActionParameters': {
            'UUID': u_first_url,
            'WFItemSpecifier': 'First Item',
            'WFInput': make_attachment(u_all_urls, 'URLs')
        }
    })

    # 7. IF: link có giá trị?
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_check_url,
            'WFControlFlowMode': 0,
            'WFCondition': 100,
            'WFInput': {
                'Type': 'Variable',
                'Variable': make_attachment(u_first_url, 'Item from List')
            }
        }
    })

    # 8. Set variable url_fetch = Item from List
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'url_fetch',
            'WFInput': make_attachment(u_first_url, 'Item from List')
        }
    })

    # 9. ELSE (Hỏi người dùng)
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_check_url,
            'WFControlFlowMode': 1
        }
    })

    # 10. Ask for input
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.ask',
        'WFWorkflowActionParameters': {
            'UUID': u_ask_input,
            'WFAskActionPrompt': f"⚡️ {shortcut_name}: Dán liên kết video vào đây:",
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
    })

    # 11. Detect link từ input
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.detect.link',
        'WFWorkflowActionParameters': {
            'UUID': u_ask_urls,
            'WFInput': make_attachment(u_ask_input, 'Provided Input')
        }
    })

    # 12. Lấy link đầu tiên từ input
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getitemfromlist',
        'WFWorkflowActionParameters': {
            'UUID': u_ask_first,
            'WFItemSpecifier': 'First Item',
            'WFInput': make_attachment(u_ask_urls, 'URLs')
        }
    })

    # 13. Set variable url_fetch = link vừa nhập
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'url_fetch',
            'WFInput': make_attachment(u_ask_first, 'Item from List')
        }
    })

    # 14. END IF (check url)
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_check_url,
            'WFControlFlowMode': 2
        }
    })

    # 15. SCREENSHOT 4: IF url_fetch contains {{open-url}}
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_open_url,
            'WFControlFlowMode': 0,
            'WFCondition': 99,
            'WFConditionalActionString': '{{open-url}}',
            'WFInput': {
                'Type': 'Variable',
                'Variable': make_var_attachment('url_fetch')
            }
        }
    })

    # 16. Replace {{open-url}} with "" in url_fetch
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.text.replace',
        'WFWorkflowActionParameters': {
            'UUID': u_replace_open,
            'CustomOutputName': 'Updated Text',
            'WFReplaceTextFind': '{{open-url}}',
            'WFReplaceTextReplace': '',
            'WFInput': make_var_attachment('url_fetch')
        }
    })

    # 17. IF Updated Text has any value
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_check_replaced,
            'WFControlFlowMode': 0,
            'WFCondition': 100,
            'WFInput': {
                'Type': 'Variable',
                'Variable': make_attachment(u_replace_open, 'Updated Text')
            }
        }
    })

    # 18. Open Updated Text
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.openurl',
        'WFWorkflowActionParameters': {
            'UUID': u_open_url,
            'WFInput': make_attachment(u_replace_open, 'Updated Text')
        }
    })

    # 19. END IF (check replaced)
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_check_replaced,
            'WFControlFlowMode': 2
        }
    })

    # 20. Stop this shortcut (trong nhánh open-url)
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.exit',
        'WFWorkflowActionParameters': {}
    })

    # 21. END IF (open-url)
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_open_url,
            'WFControlFlowMode': 2
        }
    })

    # 22. Thiết lập các nhãn điều hướng kết thúc: open_album, open_file, close
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'open_album',
            'WFInput': {'Value': {'string': '📸 Mở Album Ảnh'}, 'WFSerializationType': 'WFTextTokenString'}
        }
    })
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'open_file',
            'WFInput': {'Value': {'string': '📁 Mở ứng dụng Tệp'}, 'WFSerializationType': 'WFTextTokenString'}
        }
    })
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'close',
            'WFInput': {'Value': {'string': '❌ Đóng'}, 'WFSerializationType': 'WFTextTokenString'}
        }
    })

    # 23. Lấy biến url_fetch để gọi API
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getvariable',
        'WFWorkflowActionParameters': {
            'UUID': u_get_url,
            'CustomOutputName': 'url_fetch',
            'WFVariable': make_var_attachment('url_fetch')
        }
    })

    # 24. Download API parse
    api_string = api_base_url + '\ufffc'
    offset_key = f'{{{len(api_base_url)}, 1}}'
    actions.append({
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
                            'WFValue': {'Value': {'string': f'{shortcut_name}/8.0 iOS'}, 'WFSerializationType': 'WFTextTokenString'}
                        }
                    ]
                },
                'WFSerializationType': 'WFDictionaryFieldValue'
            },
            'WFURL': {
                'Value': {
                    'attachmentsByRange': {
                        offset_key: {
                            'OutputUUID': u_get_url,
                            'OutputName': 'url_fetch',
                            'Type': 'ActionOutput',
                            'Aggrandizements': [{
                                'Type': 'WFCoercionVariableAggrandizement',
                                'CoercionItemClass': 'WFURLContentItem'
                            }]
                        }
                    },
                    'string': api_string
                },
                'WFSerializationType': 'WFTextTokenString'
            }
        }
    })

    # 25. Lấy title
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
        'WFWorkflowActionParameters': {
            'UUID': u_title,
            'CustomOutputName': 'title',
            'WFDictionaryKey': 'title',
            'WFInput': make_attachment(u_api_res, 'api_data')
        }
    })
    # Gán biến title
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'title',
            'WFInput': make_attachment(u_title, 'title')
        }
    })

    # 26. Lấy labels
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
        'WFWorkflowActionParameters': {
            'UUID': u_labels,
            'CustomOutputName': 'labels',
            'WFDictionaryKey': 'labels',
            'WFInput': make_attachment(u_api_res, 'api_data')
        }
    })

    # 27. Lấy medias
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
        'WFWorkflowActionParameters': {
            'UUID': u_medias,
            'CustomOutputName': 'medias',
            'WFDictionaryKey': 'medias',
            'WFInput': make_attachment(u_api_res, 'api_data')
        }
    })
    # Gán biến medias
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'medias',
            'WFInput': make_attachment(u_medias, 'medias')
        }
    })

    # 28. Lấy menu_title
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
        'WFWorkflowActionParameters': {
            'UUID': u_menu_title,
            'CustomOutputName': 'menu_title',
            'WFDictionaryKey': 'menu_title',
            'WFInput': make_attachment(u_api_res, 'api_data')
        }
    })

    # 29. Choose from labels
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.choosefromlist',
        'WFWorkflowActionParameters': {
            'UUID': u_chosen_item,
            'CustomOutputName': 'Chosen Item',
            'WFInput': make_attachment(u_labels, 'labels'),
            'WFChooseFromListActionPrompt': {
                'Value': {
                    'attachmentsByRange': {
                        '{0, 1}': {'OutputUUID': u_menu_title, 'OutputName': 'menu_title', 'Type': 'ActionOutput'}
                    },
                    'string': '\ufffc'
                },
                'WFSerializationType': 'WFTextTokenString'
            },
            'WFChooseFromListActionSelectMultiple': True
        }
    })

    # Gán biến selected_item
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'selected_item',
            'WFInput': make_attachment(u_chosen_item, 'Chosen Item')
        }
    })

    # 30. Count items in selected_item -> count_select
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.count',
        'WFWorkflowActionParameters': {
            'UUID': u_count_select,
            'CustomOutputName': 'count_select',
            'WFCountType': 'Items',
            'WFInput': make_var_attachment('selected_item')
        }
    })
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'count_select',
            'WFInput': make_attachment(u_count_select, 'count_select')
        }
    })

    # 31. SCREENSHOT 4 + 3 + 1: REPEAT LOOP
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.repeat.count',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_repeat,
            'WFControlFlowMode': 0,
            'WFRepeatCount': 50
        }
    })

    # Lấy item tại vị trí Repeat Index từ selected_item -> label_now
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getitemfromlist',
        'WFWorkflowActionParameters': {
            'UUID': u_item_index,
            'CustomOutputName': 'label_now',
            'WFItemSpecifier': 'Item At Index',
            'WFItemIndex': {
                'Value': {'Type': 'RepeatIndex'},
                'WFSerializationType': 'WFTextTokenAttachment'
            },
            'WFInput': make_var_attachment('selected_item')
        }
    })
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'label_now',
            'WFInput': make_attachment(u_item_index, 'label_now')
        }
    })

    # Lấy link tải từ Dictionary medias theo khóa label_now
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
        'WFWorkflowActionParameters': {
            'UUID': u_dl_url,
            'CustomOutputName': 'dl_url',
            'WFDictionaryKey': {
                'Value': {
                    'attachmentsByRange': {
                        '{0, 1}': {'VariableName': 'label_now', 'Type': 'Variable'}
                    },
                    'string': '\ufffc'
                },
                'WFSerializationType': 'WFTextTokenString'
            },
            'WFInput': make_var_attachment('medias')
        }
    })

    # Tải media từ download url -> fetch_result
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.downloadurl',
        'WFWorkflowActionParameters': {
            'UUID': u_fetch_res,
            'CustomOutputName': 'fetch_result',
            'WFURL': {
                'Value': {
                    'attachmentsByRange': {
                        '{0, 1}': {
                            'OutputUUID': u_dl_url,
                            'OutputName': 'dl_url',
                            'Type': 'ActionOutput',
                            'Aggrandizements': [{
                                'Type': 'WFCoercionVariableAggrandizement',
                                'CoercionItemClass': 'WFURLContentItem'
                            }]
                        }
                    },
                    'string': '\ufffc'
                },
                'WFSerializationType': 'WFTextTokenString'
            }
        }
    })

    # 32. SCREENSHOT 4: IF Repeat Index is not 0 (hoặc có link hợp lệ)
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_repeat_not_first,
            'WFControlFlowMode': 0,
            'WFCondition': 100,
            'WFInput': {
                'Type': 'Variable',
                'Variable': make_attachment(u_fetch_res, 'fetch_result')
            }
        }
    })

    # SCREENSHOT 4: Match mp4|mov|jpg|jpeg|heic|png|webp|mp3|m4a in label_now
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.text.match',
        'WFWorkflowActionParameters': {
            'UUID': u_match_ext,
            'CustomOutputName': 'Matches',
            'WFMatchTextPattern': 'mp4|mov|jpg|jpeg|heic|png|webp|mp3|m4a',
            'WFMatchTextCaseSensitive': False,
            'text': make_var_attachment('label_now')
        }
    })

    # SCREENSHOT 4: Change Matches to lowercase
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.text.changecase',
        'WFWorkflowActionParameters': {
            'UUID': u_ext_lower,
            'CustomOutputName': 'ext',
            'WFTextCaseType': 'lowercase',
            'text': make_attachment(u_match_ext, 'Matches')
        }
    })

    # SCREENSHOT 4: Random number between 1 and 9999999
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.math.random',
        'WFWorkflowActionParameters': {
            'UUID': u_rand_num,
            'CustomOutputName': 'Random Number',
            'WFRandomNumberMinimum': 1,
            'WFRandomNumberMaximum': 9999999
        }
    })

    # SCREENSHOT 3: Set name of fetch_result to [prefix]--[title] - [Random Number].[ext]
    prefix = f"{shortcut_name.lower().replace(' ', '')}--"
    prefix_len = len(prefix)
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setname',
        'WFWorkflowActionParameters': {
            'UUID': u_set_name,
            'CustomOutputName': 'media_loaded',
            'WFDontIncludeFileExtension': True,
            'WFName': {
                'Value': {
                    'attachmentsByRange': {
                        f'{{{prefix_len}, 1}}': {'VariableName': 'title', 'Type': 'Variable'},
                        f'{{{prefix_len + 3}, 1}}': {'OutputUUID': u_rand_num, 'OutputName': 'Random Number', 'Type': 'ActionOutput'},
                        f'{{{prefix_len + 5}, 1}}': {'OutputUUID': u_ext_lower, 'OutputName': 'ext', 'Type': 'ActionOutput'}
                    },
                    'string': f'{prefix}\ufffc - \ufffc.\ufffc'
                },
                'WFSerializationType': 'WFTextTokenString'
            },
            'WFInput': make_attachment(u_fetch_res, 'fetch_result')
        }
    })

    # SCREENSHOT 3: IF label_now contains 🎵
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_save_type,
            'WFControlFlowMode': 0,
            'WFCondition': 99,
            'WFConditionalActionString': '🎵',
            'WFInput': {
                'Type': 'Variable',
                'Variable': make_var_attachment('label_now')
            }
        }
    })

    # SCREENSHOT 3: Save media_loaded to Documents
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.documentpicker.save',
        'WFWorkflowActionParameters': {
            'UUID': u_save_file,
            'CustomOutputName': 'Saved File',
            'WFFileDestinationPath': 'Documents',
            'WFAskWhereToSave': False,
            'WFInput': make_attachment(u_set_name, 'media_loaded')
        }
    })
    # Gán biến Saved File
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'Saved File',
            'WFInput': make_attachment(u_save_file, 'Saved File')
        }
    })

    # SCREENSHOT 3: Set variable m_file to open_file
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'm_file',
            'WFInput': make_var_attachment('open_file')
        }
    })

    # SCREENSHOT 3: OTHERWISE
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_save_type,
            'WFControlFlowMode': 1
        }
    })

    # SCREENSHOT 3: Save media_loaded to Recents
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.savetocameraroll',
        'WFWorkflowActionParameters': {
            'UUID': u_save_recents,
            'WFCameraRollSelectedGroup': 'Recents',
            'WFInput': make_attachment(u_set_name, 'media_loaded')
        }
    })

    # SCREENSHOT 3: Set variable m_album to open_album
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'm_album',
            'WFInput': make_var_attachment('open_album')
        }
    })

    # SCREENSHOT 3: END IF (save type)
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_save_type,
            'WFControlFlowMode': 2
        }
    })

    # SCREENSHOT 3: END IF (repeat not first)
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_repeat_not_first,
            'WFControlFlowMode': 2
        }
    })

    # SCREENSHOT 3 (bottom) & SCREENSHOT 2 & SCREENSHOT 1:
    # IF Repeat Index is greater than count_select
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_loop_check,
            'WFControlFlowMode': 0,
            'WFCondition': 2,  # Is Greater Than
            'WFNumberValue': {
                'Value': make_var_attachment('count_select'),
                'WFSerializationType': 'WFTextTokenAttachment'
            },
            'WFInput': {
                'Type': 'Variable',
                'Variable': {
                    'Value': {'Type': 'RepeatIndex'},
                    'WFSerializationType': 'WFTextTokenAttachment'
                }
            }
        }
    })

    # SCREENSHOT 2: Add m_album to menu_done
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.appendvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'menu_done',
            'WFInput': make_var_attachment('m_album')
        }
    })

    # SCREENSHOT 2: Add m_file to menu_done
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.appendvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'menu_done',
            'WFInput': make_var_attachment('m_file')
        }
    })

    # SCREENSHOT 2: Add close to menu_done
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.appendvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'menu_done',
            'WFInput': make_var_attachment('close')
        }
    })

    # SCREENSHOT 2: Choose from menu_done
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.choosefromlist',
        'WFWorkflowActionParameters': {
            'UUID': u_menu_select,
            'CustomOutputName': 'menu_done_select',
            'WFInput': make_var_attachment('menu_done'),
            'WFChooseFromListActionPrompt': '🎉 Tải xong! Bạn muốn làm gì tiếp theo?',
            'WFChooseFromListActionSelectMultiple': False
        }
    })
    # Gán biến menu_done_select
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'menu_done_select',
            'WFInput': make_attachment(u_menu_select, 'menu_done_select')
        }
    })

    # SCREENSHOT 2: IF menu_done_select is open_album
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_check_album,
            'WFControlFlowMode': 0,
            'WFCondition': 4,  # Is
            'WFConditionalActionString': '📸 Mở Album Ảnh',
            'WFInput': {
                'Type': 'Variable',
                'Variable': make_var_attachment('menu_done_select')
            }
        }
    })

    # SCREENSHOT 2: Open Photos
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.openapp',
        'WFWorkflowActionParameters': {
            'WFAppIdentifier': 'com.apple.mobileslideshow'
        }
    })

    # SCREENSHOT 2: END IF (album)
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_check_album,
            'WFControlFlowMode': 2
        }
    })

    # SCREENSHOT 2: IF menu_done_select is open_file
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_check_file,
            'WFControlFlowMode': 0,
            'WFCondition': 4,  # Is
            'WFConditionalActionString': '📁 Mở ứng dụng Tệp',
            'WFInput': {
                'Type': 'Variable',
                'Variable': make_var_attachment('menu_done_select')
            }
        }
    })

    # SCREENSHOT 2: Open Saved File in Finder
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.openin',
        'WFWorkflowActionParameters': {
            'WFOpenInAppIdentifier': 'com.apple.finder',
            'WFOpenInAskWhenRun': False,
            'WFInput': make_var_attachment('Saved File')
        }
    })

    # SCREENSHOT 2: END IF (file)
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_check_file,
            'WFControlFlowMode': 2
        }
    })

    # SCREENSHOT 1: Stop this shortcut
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.exit',
        'WFWorkflowActionParameters': {}
    })

    # SCREENSHOT 1: END IF (loop check)
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_loop_check,
            'WFControlFlowMode': 2
        }
    })

    # SCREENSHOT 1: END REPEAT
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.repeat.count',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_repeat,
            'WFControlFlowMode': 2
        }
    })

    all_content_classes = [
        'WFAppStoreAppContentItem', 'WFArticleContentItem', 'WFContactContentItem',
        'WFDateContentItem', 'WFEmailAddressContentItem', 'WFGenericFileContentItem',
        'WFImageContentItem', 'WFiTunesProductContentItem', 'WFLocationContentItem',
        'WFDCMapsLinkContentItem', 'WFAVAssetContentItem', 'WFPDFContentItem',
        'WFPhoneNumberContentItem', 'WFRichTextContentItem', 'WFSafariWebPageContentItem',
        'WFStringContentItem', 'WFURLContentItem'
    ]

    return {
        'WFWorkflowMinimumClientVersion': 900,
        'WFWorkflowClientVersion': '2607.1',
        'WFWorkflowClientRelease': '8.0',
        'WFWorkflowIcon': {
            'WFWorkflowIconStartColor': 4282601983,
            'WFWorkflowIconGlyphNumber': 59511
        },
        'WFWorkflowTypes': ['NCWidget', 'ActionExtension', 'QuickLook'],
        'WFWorkflowInputContentItemClasses': all_content_classes,
        'WFWorkflowActions': actions
    }

def generate_shortcut(source_file, signed_file, api_base_url, name):
    workflow = build_workflow(api_base_url=api_base_url, shortcut_name=name)
    with open(source_file, 'wb') as f:
        plistlib.dump(workflow, f)
    print(f"📦 Đã tạo source plist: {source_file} ({len(workflow['WFWorkflowActions'])} actions)")

    try:
        subprocess.run(
            ['shortcuts', 'sign', '--mode', 'anyone', '--input', source_file, '--output', signed_file],
            check=True
        )
        print(f"✅ Đã ký số thành công: {signed_file} ({os.path.getsize(signed_file)} bytes)")
    except Exception as e:
        print(f"⚠️ Không thể ký file bằng 'shortcuts sign': {e}")

if __name__ == '__main__':
    # 1. Tạo SnapAll Pro sử dụng 100% mã nguồn & cấu trúc Snap Video với API riêng của bạn
    generate_shortcut(
        source_file='SnapAll_Source.shortcut',
        signed_file='SnapAll.shortcut',
        api_base_url=DEFAULT_API_URL,
        name='SnapAll'
    )

    # 2. Tạo Snap Video bản chuẩn kiến trúc ảnh chụp sử dụng API hoạt động
    generate_shortcut(
        source_file='SnapVideo_Source.shortcut',
        signed_file='SnapVideo.shortcut',
        api_base_url=DEFAULT_API_URL,
        name='Snap Video'
    )
