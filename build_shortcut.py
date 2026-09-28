#!/usr/bin/env python3
"""
SnapAll & Snap Video Shortcut Generator
Tạo file .shortcut chuẩn kiến trúc Apple Shortcuts theo nội dung ảnh chụp Snap Video:
1. Nhận link đa nguồn (Share Sheet, Clipboard, hoặc Hỏi trực tiếp).
2. Xử lý mở link đặc biệt {{open-url}}.
3. Gọi API (snapall.vercel.app/api/parse?url=...) lấy labels + medias.
4. Lặp qua các lựa chọn (Repeat 50):
   - Lấy dl_url từ dictionary medias theo label_now.
   - Get Text từ dl_url → url_text (TEXT THUẦN TÚY để iOS hiểu).
   - Tải media từ url_text -> fetch_result.
   - Regex trích xuất đuôi từ label_now (mp4|mov|jpg|jpeg|heic|png|webp|mp3|m4a).
   - Đổi thành chữ thường (ext).
   - Sinh số ngẫu nhiên 1 - 9999999.
   - Set Name: snapall--[title] - [Random Number].[ext]
   - Phân loại lưu: 🎵 → Documents, Others → Recents.
5. Menu hoàn tất (menu_done): Mở Photos / Mở Tệp / Đóng.
"""

import plistlib
import os
import uuid
import subprocess

# ==============================================================================
# 🌐 CẤU HÌNH API RIÊNG CỦA BẠN:
# ==============================================================================
DEFAULT_API_URL = "https://snapall.vercel.app/api/parse?url="


def uid():
    return str(uuid.uuid4()).upper()


def make_action_attachment(output_uuid, output_name, coerce_class=None):
    """Tạo attachment từ ActionOutput UUID (output của action cụ thể)."""
    agg = []
    if coerce_class:
        agg = [{'Type': 'WFCoercionVariableAggrandizement', 'CoercionItemClass': coerce_class}]
    val = {
        'OutputUUID': output_uuid,
        'OutputName': output_name,
        'Type': 'ActionOutput',
    }
    if agg:
        val['Aggrandizements'] = agg
    return {'Value': val, 'WFSerializationType': 'WFTextTokenAttachment'}


def make_var_attachment(var_name, coerce_class=None):
    """Tạo attachment từ Named Variable."""
    agg = []
    if coerce_class:
        agg = [{'Type': 'WFCoercionVariableAggrandizement', 'CoercionItemClass': coerce_class}]
    val = {'VariableName': var_name, 'Type': 'Variable'}
    if agg:
        val['Aggrandizements'] = agg
    return {'Value': val, 'WFSerializationType': 'WFTextTokenAttachment'}


def make_repeat_index_attachment():
    """Tạo attachment từ Repeat Index (biến đặc biệt)."""
    return {'Value': {'Type': 'RepeatIndex'}, 'WFSerializationType': 'WFTextTokenAttachment'}


def text_token(static_str, attachments_by_range=None):
    """Tạo WFTextTokenString với text tĩnh và các attachment."""
    val = {'string': static_str}
    if attachments_by_range:
        val['attachmentsByRange'] = attachments_by_range
    return {'Value': val, 'WFSerializationType': 'WFTextTokenString'}


def build_workflow(api_base_url="https://snapall.vercel.app/api/parse?url=", shortcut_name="SnapAll"):
    actions = []

    # ─── UUIDs ───────────────────────────────────────────────────────────────
    u_link_share   = uid()
    u_clip         = uid()
    u_link_clip    = uid()
    u_combined     = uid()
    u_all_urls     = uid()
    u_first_url    = uid()

    grp_check_url  = uid()
    u_ask_input    = uid()
    u_ask_urls     = uid()
    u_ask_first    = uid()

    grp_open_url   = uid()
    u_replace_open = uid()
    grp_check_replaced = uid()

    u_get_url_var  = uid()   # getvariable url_fetch -> để build URL string
    u_api_res      = uid()   # API call result
    u_title        = uid()
    u_labels       = uid()
    u_medias       = uid()
    u_menu_title   = uid()
    u_chosen_item  = uid()
    u_count_select = uid()

    grp_repeat     = uid()
    u_item_index   = uid()   # label_now
    u_dl_url       = uid()   # value from dictionary (raw object)
    u_url_text     = uid()   # gettext dl_url → text string (QUAN TRỌNG cho iOS)
    u_fetch_res    = uid()   # downloadurl từ url_text

    grp_if_valid   = uid()   # IF fetch_result has any value
    u_match_ext    = uid()
    u_ext_lower    = uid()
    u_rand_num     = uid()
    u_set_name     = uid()

    grp_save_type  = uid()
    u_save_file    = uid()
    u_save_recents = uid()

    grp_loop_done  = uid()
    u_menu_select  = uid()
    grp_check_album = uid()
    grp_check_file  = uid()

    # ─── 0. Comment ─────────────────────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.comment',
        'WFWorkflowActionParameters': {
            'WFCommentActionText': (
                f"⚡️ {shortcut_name} v8.0 Pro\n"
                "• Kiến trúc 100% từ Snap Video (iOS Shortcuts).\n"
                "• API riêng: snapall.vercel.app (không quảng cáo).\n"
                "• Share Sheet / Clipboard / Hỏi trực tiếp.\n"
                "• Hỗ trợ TikTok không logo, Facebook HD, MP3."
            )
        }
    })

    # ─── 1. Detect URLs từ Share Sheet ──────────────────────────────────────
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

    # ─── 2. Lấy Clipboard ───────────────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getclipboard',
        'WFWorkflowActionParameters': {'UUID': u_clip}
    })

    # ─── 3. Detect URLs từ Clipboard ────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.detect.link',
        'WFWorkflowActionParameters': {
            'UUID': u_link_clip,
            'CustomOutputName': 'URLs Clipboard',
            'WFInput': make_action_attachment(u_clip, 'Clipboard')
        }
    })

    # ─── 4. Ghép 2 nguồn URL thành 1 text ───────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.gettext',
        'WFWorkflowActionParameters': {
            'UUID': u_combined,
            'WFTextActionText': text_token('\ufffc\n\ufffc', {
                '{0, 1}': {'OutputUUID': u_link_share, 'OutputName': 'URLs Share', 'Type': 'ActionOutput'},
                '{2, 1}': {'OutputUUID': u_link_clip,  'OutputName': 'URLs Clipboard', 'Type': 'ActionOutput'},
            })
        }
    })

    # ─── 5. Detect URLs từ text ghép ────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.detect.link',
        'WFWorkflowActionParameters': {
            'UUID': u_all_urls,
            'WFInput': make_action_attachment(u_combined, 'Text')
        }
    })

    # ─── 6. Lấy URL đầu tiên ────────────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getitemfromlist',
        'WFWorkflowActionParameters': {
            'UUID': u_first_url,
            'WFItemSpecifier': 'First Item',
            'WFInput': make_action_attachment(u_all_urls, 'URLs')
        }
    })

    # ─── 7. IF: URL đầu tiên có giá trị? ────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_check_url,
            'WFControlFlowMode': 0,
            'WFCondition': 100,   # has any value
            'WFInput': {
                'Type': 'Variable',
                'Variable': make_action_attachment(u_first_url, 'Item from List')
            }
        }
    })

    # ─── 8. Set url_fetch = first URL ───────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'url_fetch',
            'WFInput': make_action_attachment(u_first_url, 'Item from List')
        }
    })

    # ─── 9. ELSE: Hỏi người dùng ────────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_check_url,
            'WFControlFlowMode': 1
        }
    })

    # ─── 10. Ask for Text ────────────────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.ask',
        'WFWorkflowActionParameters': {
            'UUID': u_ask_input,
            'WFAskActionPrompt': f"⚡️ {shortcut_name}: Dán liên kết video vào đây:",
            'WFAskActionDefaultAnswer': {
                'Value': {
                    'string': '\ufffc',
                    'attachmentsByRange': {'{0, 1}': {'Type': 'Clipboard'}}
                },
                'WFSerializationType': 'WFTextTokenString'
            },
            'WFAllowsMultilineText': False
        }
    })

    # ─── 11. Detect URLs từ input người dùng ────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.detect.link',
        'WFWorkflowActionParameters': {
            'UUID': u_ask_urls,
            'WFInput': make_action_attachment(u_ask_input, 'Provided Input')
        }
    })

    # ─── 12. Lấy URL đầu tiên từ input ──────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getitemfromlist',
        'WFWorkflowActionParameters': {
            'UUID': u_ask_first,
            'WFItemSpecifier': 'First Item',
            'WFInput': make_action_attachment(u_ask_urls, 'URLs')
        }
    })

    # ─── 13. Set url_fetch = URL từ input ───────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'url_fetch',
            'WFInput': make_action_attachment(u_ask_first, 'Item from List')
        }
    })

    # ─── 14. END IF (check url) ──────────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_check_url,
            'WFControlFlowMode': 2
        }
    })

    # ─── 15. IF url_fetch contains {{open-url}} ──────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_open_url,
            'WFControlFlowMode': 0,
            'WFCondition': 99,   # contains
            'WFConditionalActionString': '{{open-url}}',
            'WFInput': {
                'Type': 'Variable',
                'Variable': make_var_attachment('url_fetch')
            }
        }
    })

    # ─── 16. Replace {{open-url}} với "" trong url_fetch ─────────────────────
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

    # ─── 17. IF Updated Text is not anything (tức là KHÔNG RỖNG) ────────────
    # Snap Video gốc: "If Updated Text is not anything" → Open URL
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_check_replaced,
            'WFControlFlowMode': 0,
            'WFCondition': 101,   # does not have any value (i.e. is not empty)
            # NOTE: "is not anything" = WFCondition 101 (does not have value)
            # Nhưng thực ra Snap Video check "is not anything" tức là URL hợp lệ đã được extract
            # Để phù hợp iOS: check has any value (100)
            'WFInput': {
                'Type': 'Variable',
                'Variable': make_action_attachment(u_replace_open, 'Updated Text')
            }
        }
    })

    # ─── 18. Open URL ─────────────────────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.openurl',
        'WFWorkflowActionParameters': {
            'WFInput': make_action_attachment(u_replace_open, 'Updated Text')
        }
    })

    # ─── 19. END IF (check replaced) ─────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_check_replaced,
            'WFControlFlowMode': 2
        }
    })

    # ─── 20. Stop this shortcut (kết thúc nhánh open-url) ───────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.exit',
        'WFWorkflowActionParameters': {}
    })

    # ─── 21. END IF (open-url) ───────────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_open_url,
            'WFControlFlowMode': 2
        }
    })

    # ─── 22-24. Set điều hướng cuối (open_album, open_file, close) ───────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'open_album',
            'WFInput': text_token('📸 Mở Album Ảnh')
        }
    })
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'open_file',
            'WFInput': text_token('📁 Mở ứng dụng Tệp')
        }
    })
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'close',
            'WFInput': text_token('❌ Đóng')
        }
    })

    # ─── 25. Get Variable url_fetch → output để dùng trong URL string ────────
    # Cần thiết vì iOS Shortcuts cần ActionOutput reference chứ không dùng thẳng VariableName
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getvariable',
        'WFWorkflowActionParameters': {
            'UUID': u_get_url_var,
            'CustomOutputName': 'url_fetch_out',
            'WFVariable': make_var_attachment('url_fetch')
        }
    })

    # ─── 26. Get URL Content (API parse) ─────────────────────────────────────
    # Tạo URL: api_base_url + url_fetch_out (coerced to URL text)
    api_offset = len(api_base_url)   # offset của placeholder \ufffc trong URL string
    api_url_string = api_base_url + '\ufffc'
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.downloadurl',
        'WFWorkflowActionParameters': {
            'UUID': u_api_res,
            'CustomOutputName': 'api_data',
            'WFHTTPHeaders': {
                'Value': {
                    'WFDictionaryFieldValueItems': [
                        {
                            'WFKey': text_token('User-Agent'),
                            'WFItemType': 0,
                            'WFValue': text_token(f'{shortcut_name}/8.0 iOS')
                        }
                    ]
                },
                'WFSerializationType': 'WFDictionaryFieldValue'
            },
            'WFURL': text_token(api_url_string, {
                f'{{{api_offset}, 1}}': {
                    'OutputUUID': u_get_url_var,
                    'OutputName': 'url_fetch_out',
                    'Type': 'ActionOutput',
                    'Aggrandizements': [{
                        'Type': 'WFCoercionVariableAggrandizement',
                        'CoercionItemClass': 'WFURLContentItem'
                    }]
                }
            })
        }
    })

    # ─── 27. Lấy title từ api_data ────────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
        'WFWorkflowActionParameters': {
            'UUID': u_title,
            'CustomOutputName': 'title',
            'WFDictionaryKey': 'title',
            'WFInput': make_action_attachment(u_api_res, 'api_data')
        }
    })
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'title',
            'WFInput': make_action_attachment(u_title, 'title')
        }
    })

    # ─── 28. Lấy labels từ api_data ───────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
        'WFWorkflowActionParameters': {
            'UUID': u_labels,
            'CustomOutputName': 'labels',
            'WFDictionaryKey': 'labels',
            'WFInput': make_action_attachment(u_api_res, 'api_data')
        }
    })

    # ─── 29. Lấy medias từ api_data ───────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
        'WFWorkflowActionParameters': {
            'UUID': u_medias,
            'CustomOutputName': 'medias',
            'WFDictionaryKey': 'medias',
            'WFInput': make_action_attachment(u_api_res, 'api_data')
        }
    })
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'medias',
            'WFInput': make_action_attachment(u_medias, 'medias')
        }
    })

    # ─── 30. Lấy menu_title từ api_data ──────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
        'WFWorkflowActionParameters': {
            'UUID': u_menu_title,
            'CustomOutputName': 'menu_title',
            'WFDictionaryKey': 'menu_title',
            'WFInput': make_action_attachment(u_api_res, 'api_data')
        }
    })

    # ─── 31. Choose from labels (menu tải) ───────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.choosefromlist',
        'WFWorkflowActionParameters': {
            'UUID': u_chosen_item,
            'CustomOutputName': 'Chosen Item',
            'WFInput': make_action_attachment(u_labels, 'labels'),
            'WFChooseFromListActionPrompt': text_token('\ufffc', {
                '{0, 1}': {'OutputUUID': u_menu_title, 'OutputName': 'menu_title', 'Type': 'ActionOutput'}
            }),
            'WFChooseFromListActionSelectMultiple': True
        }
    })
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'selected_item',
            'WFInput': make_action_attachment(u_chosen_item, 'Chosen Item')
        }
    })

    # ─── 32. Count selected items ─────────────────────────────────────────────
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
            'WFInput': make_action_attachment(u_count_select, 'count_select')
        }
    })

    # ─── 33. REPEAT 50 ───────────────────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.repeat.count',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_repeat,
            'WFControlFlowMode': 0,
            'WFRepeatCount': 50
        }
    })

    # ─── 34. Lấy label tại vị trí Repeat Index ───────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getitemfromlist',
        'WFWorkflowActionParameters': {
            'UUID': u_item_index,
            'CustomOutputName': 'label_now',
            'WFItemSpecifier': 'Item At Index',
            'WFItemIndex': make_repeat_index_attachment(),
            'WFInput': make_var_attachment('selected_item')
        }
    })
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'label_now',
            'WFInput': make_action_attachment(u_item_index, 'label_now')
        }
    })

    # ─── 35. Lấy dl_url từ dictionary medias (theo key label_now) ────────────
    # Đây trả về object, CHƯA phải text URL thuần túy
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
        'WFWorkflowActionParameters': {
            'UUID': u_dl_url,
            'CustomOutputName': 'dl_url',
            'WFDictionaryKey': text_token('\ufffc', {
                '{0, 1}': {'VariableName': 'label_now', 'Type': 'Variable'}
            }),
            'WFInput': make_var_attachment('medias')
        }
    })

    # ─── 36. Get Text từ dl_url → url_text (ĐÂY LÀ FIX CHÍNH CHO iOS) ───────
    # Trên iOS, khi lấy value từ Dictionary, kết quả là JSON value object chứ không phải URL.
    # Cần dùng "Text" action để convert thành string thuần túy rồi mới dùng làm URL.
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.gettext',
        'WFWorkflowActionParameters': {
            'UUID': u_url_text,
            'CustomOutputName': 'url_text',
            'WFTextActionText': text_token('\ufffc', {
                '{0, 1}': {'OutputUUID': u_dl_url, 'OutputName': 'dl_url', 'Type': 'ActionOutput'}
            })
        }
    })

    # ─── 37. Get URL Content (tải file media) từ url_text ────────────────────
    # Dùng url_text (text thuần túy) coerce sang URL → iOS không báo lỗi nữa
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.downloadurl',
        'WFWorkflowActionParameters': {
            'UUID': u_fetch_res,
            'CustomOutputName': 'fetch_result',
            'WFURL': text_token('\ufffc', {
                '{0, 1}': {
                    'OutputUUID': u_url_text,
                    'OutputName': 'url_text',
                    'Type': 'ActionOutput',
                    'Aggrandizements': [{
                        'Type': 'WFCoercionVariableAggrandizement',
                        'CoercionItemClass': 'WFURLContentItem'
                    }]
                }
            })
        }
    })

    # ─── 38. IF fetch_result has any value ───────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_if_valid,
            'WFControlFlowMode': 0,
            'WFCondition': 100,   # has any value
            'WFInput': {
                'Type': 'Variable',
                'Variable': make_action_attachment(u_fetch_res, 'fetch_result')
            }
        }
    })

    # ─── 39. Match extension trong label_now ─────────────────────────────────
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

    # ─── 40. Change Matches to lowercase → ext ───────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.text.changecase',
        'WFWorkflowActionParameters': {
            'UUID': u_ext_lower,
            'CustomOutputName': 'ext',
            'WFTextCaseType': 'lowercase',
            'text': make_action_attachment(u_match_ext, 'Matches')
        }
    })

    # ─── 41. Random number 1 - 9999999 ───────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.math.random',
        'WFWorkflowActionParameters': {
            'UUID': u_rand_num,
            'CustomOutputName': 'Random Number',
            'WFRandomNumberMinimum': 1,
            'WFRandomNumberMaximum': 9999999
        }
    })

    # ─── 42. Set Name: [prefix]--[title] - [Random Number].[ext] ─────────────
    # prefix = "snapall--" = 9 chars
    # string = "snapall--\ufffc - \ufffc.\ufffc"
    # indexes: [0..8]=prefix, [9]=title, [10]=' ', [11]='-', [12]=' ', [13]=rand, [14]='.', [15]=ext
    prefix = f"{shortcut_name.lower().replace(' ', '')}--"
    p = len(prefix)   # e.g. "snapall--" = 9
    # Offsets trong string f"{prefix}\ufffc - \ufffc.\ufffc":
    # title at p, rand at p+4, ext at p+6
    name_string = f"{prefix}\ufffc - \ufffc.\ufffc"
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setname',
        'WFWorkflowActionParameters': {
            'UUID': u_set_name,
            'CustomOutputName': 'media_loaded',
            'WFDontIncludeFileExtension': True,
            'WFName': text_token(name_string, {
                f'{{{p}, 1}}':   {'VariableName': 'title', 'Type': 'Variable'},
                f'{{{p+4}, 1}}': {'OutputUUID': u_rand_num, 'OutputName': 'Random Number', 'Type': 'ActionOutput'},
                f'{{{p+6}, 1}}': {'OutputUUID': u_ext_lower, 'OutputName': 'ext', 'Type': 'ActionOutput'},
            }),
            'WFInput': make_action_attachment(u_fetch_res, 'fetch_result')
        }
    })

    # ─── 43. IF label_now contains 🎵 → Lưu vào Documents ───────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_save_type,
            'WFControlFlowMode': 0,
            'WFCondition': 99,   # contains
            'WFConditionalActionString': '🎵',
            'WFInput': {
                'Type': 'Variable',
                'Variable': make_var_attachment('label_now')
            }
        }
    })

    # ─── 44. Save to Documents ────────────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.documentpicker.save',
        'WFWorkflowActionParameters': {
            'UUID': u_save_file,
            'CustomOutputName': 'Saved File',
            'WFFileDestinationPath': 'Documents',
            'WFAskWhereToSave': False,
            'WFInput': make_action_attachment(u_set_name, 'media_loaded')
        }
    })
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'Saved File',
            'WFInput': make_action_attachment(u_save_file, 'Saved File')
        }
    })

    # ─── 45. Set m_file = open_file ───────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'm_file',
            'WFInput': make_var_attachment('open_file')
        }
    })

    # ─── 46. OTHERWISE ────────────────────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_save_type,
            'WFControlFlowMode': 1
        }
    })

    # ─── 47. Save to Recents (Photos) ────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.savetocameraroll',
        'WFWorkflowActionParameters': {
            'UUID': u_save_recents,
            'WFCameraRollSelectedGroup': 'Recents',
            'WFInput': make_action_attachment(u_set_name, 'media_loaded')
        }
    })

    # ─── 48. Set m_album = open_album ─────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'm_album',
            'WFInput': make_var_attachment('open_album')
        }
    })

    # ─── 49. END IF (save type) ───────────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_save_type,
            'WFControlFlowMode': 2
        }
    })

    # ─── 50. END IF (if fetch_result valid) ──────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_if_valid,
            'WFControlFlowMode': 2
        }
    })

    # ─── 51. IF Repeat Index > count_select → Thoát vòng lặp ─────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_loop_done,
            'WFControlFlowMode': 0,
            'WFCondition': 2,   # Is Greater Than
            'WFNumberValue': make_var_attachment('count_select'),
            'WFInput': {
                'Type': 'Variable',
                'Variable': make_repeat_index_attachment()
            }
        }
    })

    # ─── 52. Add m_album to menu_done ─────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.appendvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'menu_done',
            'WFInput': make_var_attachment('m_album')
        }
    })

    # ─── 53. Add m_file to menu_done ──────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.appendvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'menu_done',
            'WFInput': make_var_attachment('m_file')
        }
    })

    # ─── 54. Add close to menu_done ───────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.appendvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'menu_done',
            'WFInput': make_var_attachment('close')
        }
    })

    # ─── 55. Choose from menu_done ────────────────────────────────────────────
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
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
        'WFWorkflowActionParameters': {
            'WFVariableName': 'menu_done_select',
            'WFInput': make_action_attachment(u_menu_select, 'menu_done_select')
        }
    })

    # ─── 56. IF menu_done_select is open_album ───────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_check_album,
            'WFControlFlowMode': 0,
            'WFCondition': 4,   # Is
            'WFConditionalActionString': '📸 Mở Album Ảnh',
            'WFInput': {
                'Type': 'Variable',
                'Variable': make_var_attachment('menu_done_select')
            }
        }
    })

    # ─── 57. Open Photos app ──────────────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.openapp',
        'WFWorkflowActionParameters': {
            'WFAppIdentifier': 'com.apple.mobileslideshow'
        }
    })

    # ─── 58. END IF (album) ───────────────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_check_album,
            'WFControlFlowMode': 2
        }
    })

    # ─── 59. IF menu_done_select is open_file ────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_check_file,
            'WFControlFlowMode': 0,
            'WFCondition': 4,   # Is
            'WFConditionalActionString': '📁 Mở ứng dụng Tệp',
            'WFInput': {
                'Type': 'Variable',
                'Variable': make_var_attachment('menu_done_select')
            }
        }
    })

    # ─── 60. Open Saved File in Files app ────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.openin',
        'WFWorkflowActionParameters': {
            'WFOpenInAppIdentifier': 'com.apple.DocumentsApp',
            'WFOpenInAskWhenRun': False,
            'WFInput': make_var_attachment('Saved File')
        }
    })

    # ─── 61. END IF (file) ────────────────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_check_file,
            'WFControlFlowMode': 2
        }
    })

    # ─── 62. Stop this shortcut ───────────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.exit',
        'WFWorkflowActionParameters': {}
    })

    # ─── 63. END IF (loop done) ───────────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_loop_done,
            'WFControlFlowMode': 2
        }
    })

    # ─── 64. END REPEAT ───────────────────────────────────────────────────────
    actions.append({
        'WFWorkflowActionIdentifier': 'is.workflow.actions.repeat.count',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': grp_repeat,
            'WFControlFlowMode': 2
        }
    })

    # ─── Workflow metadata ────────────────────────────────────────────────────
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
        print(f"⚠️  Không thể ký bằng 'shortcuts sign': {e}")


if __name__ == '__main__':
    # 1. SnapAll Pro – API riêng snapall.vercel.app
    generate_shortcut(
        source_file='SnapAll_Source.shortcut',
        signed_file='SnapAll.shortcut',
        api_base_url=DEFAULT_API_URL,
        name='SnapAll'
    )

    # 2. Snap Video – cùng kiến trúc, cùng API (để tham khảo / thay thế Snap Video gốc)
    generate_shortcut(
        source_file='SnapVideo_Source.shortcut',
        signed_file='SnapVideo.shortcut',
        api_base_url=DEFAULT_API_URL,
        name='Snap Video'
    )
