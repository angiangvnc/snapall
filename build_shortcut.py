#!/usr/bin/env python3
"""
SnapAll v9.0 – Clone 100% cấu trúc Snap Video thực tế (đọc từ app Shortcuts macOS).
Chỉ thay đổi duy nhất: API endpoint trỏ về snapall.vercel.app/api/parse.

API Response Schema (phải trả về JSON với các field):
{
  "labels": ["🎬 Tải Video HD mp4", "🎵 Trích xuất Âm thanh mp3"],
  "medias": {"🎬 Tải Video HD mp4": "https://...", ...},
  "title": "Tên video",
  "menu_title": "⚡️ Chọn định dạng:",
  "open_album": "📸 Mở Album",
  "open_file": "📁 Mở Tệp",
  "close": "❌ Đóng",
  "menu_done_title": "🎉 Tải xong!",
  "select_multiple": true/false,
  "skip_select": true/false
}
"""

import plistlib
import os
import uuid
import subprocess

DEFAULT_API_URL = "https://snapall.vercel.app/api/parse"


def uid():
    return str(uuid.uuid4()).upper()


# ──────────────────────────────────────────────────────────────────────────────
# Helper: tạo WFTextTokenAttachment từ ActionOutput UUID
# ──────────────────────────────────────────────────────────────────────────────
def action_out(output_uuid, output_name, aggrandizements=None):
    val = {"OutputUUID": output_uuid, "OutputName": output_name, "Type": "ActionOutput"}
    if aggrandizements:
        val["Aggrandizements"] = aggrandizements
    return {"Value": val, "WFSerializationType": "WFTextTokenAttachment"}


# Aggrandizement: coerce to string
def agg_str():
    return {"Type": "WFCoercionVariableAggrandizement", "CoercionItemClass": "WFStringContentItem"}


# Aggrandizement: coerce to URL
def agg_url():
    return {"Type": "WFCoercionVariableAggrandizement", "CoercionItemClass": "WFURLContentItem"}


# Aggrandizement: coerce to Dictionary then extract key
def agg_dict_key(key):
    return [
        {"Type": "WFCoercionVariableAggrandizement", "CoercionItemClass": "WFDictionaryContentItem"},
        {"Type": "WFDictionaryValueVariableAggrandizement", "DictionaryKey": key},
    ]


# Helper: variable reference (named variable)
def var_ref(name, aggrandizements=None):
    val = {"VariableName": name, "Type": "Variable"}
    if aggrandizements:
        val["Aggrandizements"] = aggrandizements
    return {"Value": val, "WFSerializationType": "WFTextTokenAttachment"}


# Helper: Repeat Index reference
def repeat_index_ref():
    return {"Value": {"VariableName": "Repeat Index", "Type": "Variable"}, "WFSerializationType": "WFTextTokenAttachment"}


# Helper: text token với attachments
def text_tok(s, attachments=None):
    val = {"string": s}
    if attachments:
        val["attachmentsByRange"] = attachments
    return {"Value": val, "WFSerializationType": "WFTextTokenString"}


def build_workflow(api_url=DEFAULT_API_URL, shortcut_name="SnapAll"):
    A = []  # actions list

    # ── UUIDs ─────────────────────────────────────────────────────────────────
    u_setting         = uid()
    u_b64_input       = uid()   # base64 encode input url
    u_api_url         = uid()   # URL action: api_url + b64
    u_fetch_result    = uid()   # downloadurl → fetch_result (= api_data)
    u_item_from_list  = uid()   # getitemfromlist (selected_item từ If-result)
    u_url_media       = uid()   # getvalueforkey → url_media
    u_b64_media       = uid()   # base64 encode url_media
    u_api_url2        = uid()   # URL action: download_url + b64
    u_count_select    = uid()   # count
    u_match_ext       = uid()   # text.match
    u_ext             = uid()   # text.changecase → ext
    u_rand_num        = uid()   # number.random
    u_media_loaded    = uid()   # setitemname → media_loaded
    u_saved_file      = uid()   # documentpicker.save → Saved File
    u_menu_select     = uid()   # choosefromlist → menu_done_select

    # Group IDs (for conditional blocks)
    g_repeat          = uid()
    g_fetch_is_json   = uid()   # IF fetch_result.ext == "json"
    g_reload          = uid()   # IF fetch_result["reload"] has value
    g_url_is_1        = uid()   # IF Repeat Index is 1 (first iteration)
    g_skip_select     = uid()   # IF api_result["skip_select"]
    g_select_multiple = uid()   # IF api_result["select_multiple"]
    g_url_fetch_val   = uid()   # IF url_fetch has value (before download)
    g_url_contains_op = uid()   # IF url_fetch contains {{open-url}}
    g_url_fetch_val2  = uid()   # IF url_fetch has value (ELSE branch)
    g_url_contains2   = uid()   # IF url_fetch contains ... (ELSE branch)
    g_open_url        = uid()   # IF url_fetch contains {{open-url}} (2)
    g_has_fetch       = uid()   # IF fetch_result (media) has any value
    g_is_audio        = uid()   # IF label_now contains 🎵
    g_loop_done       = uid()   # IF Repeat Index > count_select
    g_open_album      = uid()   # IF menu_done_select == open_album
    g_open_file       = uid()   # IF menu_done_select == open_file

    # ── [0] Comment ───────────────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.comment",
        "WFWorkflowActionParameters": {
            "WFCommentActionText": (
                f"⚡️ {shortcut_name} v9.0\n"
                "Kiến trúc clone 100% từ Snap Video thực tế.\n"
                f"API: {api_url}"
            )
        }
    })

    # ── [1] Dictionary: setting ───────────────────────────────────────────────
    # Snap Video gốc: setting chứa url_red, lang, ask_format, show_menu, skip_update, url64, close, open_album, open_file, menu_done_title
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.dictionary",
        "WFWorkflowActionParameters": {
            "UUID": u_setting,
            "CustomOutputName": "setting",
            "WFItems": {
                "Value": {
                    "WFDictionaryFieldValueItems": [
                        {
                            "WFItemType": 0,
                            "WFKey": text_tok("url_red"),
                            "WFValue": text_tok(api_url + "?b64=")
                        },
                        {
                            "WFItemType": 0,
                            "WFKey": text_tok("url64"),
                            "WFValue": text_tok(api_url + "?b64=")
                        },
                        {
                            "WFItemType": 0,
                            "WFKey": text_tok("lang"),
                            "WFValue": text_tok("vi")
                        },
                        {
                            "WFItemType": 0,
                            "WFKey": text_tok("ask_format"),
                            "WFValue": text_tok("")
                        },
                        {
                            "WFItemType": 0,
                            "WFKey": text_tok("show_menu"),
                            "WFValue": text_tok("")
                        },
                        {
                            "WFItemType": 0,
                            "WFKey": text_tok("skip_update"),
                            "WFValue": text_tok("")
                        },
                        {
                            "WFItemType": 0,
                            "WFKey": text_tok("close"),
                            "WFValue": text_tok("❌ Đóng")
                        },
                        {
                            "WFItemType": 0,
                            "WFKey": text_tok("open_album"),
                            "WFValue": text_tok("📸 Mở Album Ảnh")
                        },
                        {
                            "WFItemType": 0,
                            "WFKey": text_tok("open_file"),
                            "WFValue": text_tok("📁 Mở ứng dụng Tệp")
                        },
                        {
                            "WFItemType": 0,
                            "WFKey": text_tok("menu_done_title"),
                            "WFValue": text_tok("🎉 Tải xong! Bạn muốn làm gì?")
                        },
                    ]
                },
                "WFSerializationType": "WFDictionaryFieldValue"
            }
        }
    })

    # ── [2] Comment: nhập URL ─────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.comment",
        "WFWorkflowActionParameters": {
            "WFCommentActionText": "=== PHẦN 1: NHẬN URL VÀO ==="
        }
    })

    # ── [3] Base64 encode shortcut input (Share Sheet / Clipboard) ────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.base64encode",
        "WFWorkflowActionParameters": {
            "UUID": u_b64_input,
            "WFBase64LineBreakMode": "None",
            "WFEncodeMode": "Encode",
            "WFInput": {
                "Value": {"Type": "ExtensionInput"},
                "WFSerializationType": "WFTextTokenAttachment"
            }
        }
    })

    # ── [4] URL action: api_url + b64_input ───────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.url",
        "WFWorkflowActionParameters": {
            "UUID": u_api_url,
            "WFURLActionURL": text_tok(
                "\ufffc\ufffc",
                {
                    "{0, 1}": {
                        "VariableName": "setting",
                        "Type": "Variable",
                        "Aggrandizements": agg_dict_key("url_red")
                    },
                    "{1, 1}": {
                        "OutputUUID": u_b64_input,
                        "OutputName": "Đã mã hóa Base64",
                        "Type": "ActionOutput"
                    }
                }
            )
        }
    })

    # ── [5] URL Encode (không dùng, giữ để đúng thứ tự) ──────────────────────
    # Snap Video có thêm urlencode action ở đây nhưng thực ra dùng b64 nên skip
    # Thay bằng setvariable url_fetch = URL output của action 4

    # ── [5] Set url_fetch = URL (output của action 4) ─────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "url_fetch",
            "WFInput": action_out(u_api_url, "URL")
        }
    })

    # ── [6] Set main_json = setting ──────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "main_json",
            "WFInput": action_out(u_setting, "setting")
        }
    })

    # ── [7] REPEAT 100 ────────────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.repeat.count",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_repeat,
            "WFControlFlowMode": 0,
            "WFRepeatCount": 100
        }
    })

    # ── [8] Get URL Content (call API): url_fetch → fetch_result ─────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.downloadurl",
        "WFWorkflowActionParameters": {
            "UUID": u_fetch_result,
            "CustomOutputName": "fetch_result",
            "ShowHeaders": False,
            "WFHTTPHeaders": {
                "Value": {
                    "WFDictionaryFieldValueItems": [
                        {
                            "WFKey": text_tok("User-Agent"),
                            "WFItemType": 0,
                            "WFValue": text_tok(f"Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Safari/604.1 {shortcut_name}/9.0")
                        }
                    ]
                },
                "WFSerializationType": "WFDictionaryFieldValue"
            },
            "WFURL": text_tok("\ufffc", {
                "{0, 1}": {"OutputUUID": u_api_url, "OutputName": "URL", "Type": "ActionOutput"}
            })
        }
    })

    # ── [9] IF fetch_result.extension == "json" ───────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_fetch_is_json,
            "WFControlFlowMode": 0,
            "WFCondition": 4,   # Is
            "WFConditionalActionString": "json",
            "WFInput": {
                "Type": "Variable",
                "Variable": action_out(u_fetch_result, "fetch_result", [
                    {"Type": "WFCoercionVariableAggrandizement", "CoercionItemClass": "WFGenericFileContentItem"},
                    {"PropertyUserInfo": "WFFileExtensionProperty", "Type": "WFPropertyVariableAggrandizement", "PropertyName": "File Extension"}
                ])
            }
        }
    })

    # ── [10] IF fetch_result["reload"] has value ──────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_reload,
            "WFControlFlowMode": 0,
            "WFCondition": 100,   # has any value
            "WFInput": {
                "Type": "Variable",
                "Variable": action_out(u_fetch_result, "fetch_result", agg_dict_key("reload"))
            }
        }
    })

    # ── [11] Run Shortcut (reload → tự gọi lại) ──────────────────────────────
    # Trong SnapAll không có reload, nhưng để đúng kiến trúc ta dùng exit thay
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.exit",
        "WFWorkflowActionParameters": {}
    })

    # ── [12] END IF reload ────────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_reload,
            "WFControlFlowMode": 2
        }
    })

    # ── [13] END IF fetch_is_json ─────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_fetch_is_json,
            "WFControlFlowMode": 2
        }
    })

    # ── [14] IF Repeat Index is 1 (first pass) ────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_url_is_1,
            "WFControlFlowMode": 0,
            "WFCondition": 4,   # Is
            "WFNumberValue": "1",
            "WFInput": {
                "Type": "Variable",
                "Variable": repeat_index_ref()
            }
        }
    })

    # ── [15] Set api_result = fetch_result ────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "api_result",
            "WFInput": action_out(u_fetch_result, "fetch_result")
        }
    })

    # ── [16] IF api_result["skip_select"] has value ───────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_skip_select,
            "WFControlFlowMode": 0,
            "WFCondition": 100,
            "WFInput": {
                "Type": "Variable",
                "Variable": var_ref("api_result", agg_dict_key("skip_select"))
            }
        }
    })

    # ── [17] Set selected_item = api_result["labels"] (auto-select all) ───────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "selected_item",
            "WFInput": var_ref("api_result", agg_dict_key("labels"))
        }
    })

    # ── [18] ELSE ─────────────────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_skip_select,
            "WFControlFlowMode": 1
        }
    })

    # ── [19] IF api_result["select_multiple"] has value ───────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "UUID": uid(),
            "GroupingIdentifier": g_select_multiple,
            "WFControlFlowMode": 0,
            "WFCondition": 100,
            "WFInput": {
                "Type": "Variable",
                "Variable": var_ref("api_result", agg_dict_key("select_multiple"))
            }
        }
    })

    # ── [20] Choose from list (multiple select) ───────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefromlist",
        "WFWorkflowActionParameters": {
            "WFInput": var_ref("api_result", agg_dict_key("labels")),
            "WFChooseFromListActionPrompt": text_tok("\ufffc", {
                "{0, 1}": action_out(u_fetch_result, "fetch_result", agg_dict_key("menu_title"))
            }),
            "WFChooseFromListActionSelectMultiple": True,
            "WFChooseFromListActionSelectAll": True
        }
    })

    # ── [21] ELSE ─────────────────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_select_multiple,
            "WFControlFlowMode": 1
        }
    })

    # ── [22] Choose from list (single select) ────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefromlist",
        "WFWorkflowActionParameters": {
            "WFInput": var_ref("api_result", agg_dict_key("labels")),
            "WFChooseFromListActionPrompt": text_tok("\ufffc", {
                "{0, 1}": action_out(u_fetch_result, "fetch_result", agg_dict_key("menu_title"))
            }),
            "WFChooseFromListActionSelectMultiple": False
        }
    })

    # ── [23] END IF select_multiple ───────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_select_multiple,
            "WFControlFlowMode": 2
        }
    })

    # ── [24] END IF skip_select ───────────────────────────────────────────────
    # Lấy kết quả If → selected_item
    _u_if_result = uid()
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "UUID": _u_if_result,
            "GroupingIdentifier": g_skip_select,
            "WFControlFlowMode": 2
        }
    })

    # ── [25] Set selected_item = If result ───────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "selected_item",
            "WFInput": action_out(_u_if_result, "Nếu kết quả")
        }
    })

    # ── [26] END IF Repeat Index == 1 ────────────────────────────────────────
    _u_if_idx1_end = uid()
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "UUID": _u_if_idx1_end,
            "GroupingIdentifier": g_url_is_1,
            "WFControlFlowMode": 2
        }
    })

    # ── [27] Set label_now = Item from selected_item at Repeat Index ──────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.getitemfromlist",
        "WFWorkflowActionParameters": {
            "UUID": u_item_from_list,
            "CustomOutputName": "Mục từ danh sách",
            "WFItemSpecifier": "Item At Index",
            "WFItemIndex": repeat_index_ref(),
            "WFInput": var_ref("selected_item")
        }
    })
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "label_now",
            "WFInput": action_out(u_item_from_list, "Mục từ danh sách")
        }
    })

    # ── [28] count selected_item → count_select ───────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.count",
        "WFWorkflowActionParameters": {
            "UUID": u_count_select,
            "CustomOutputName": "count_select",
            "WFCountType": "Items",
            "Input": var_ref("selected_item")
        }
    })

    # ── [29] IF Repeat Index < count_select (còn item để tải) ─────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_url_fetch_val,
            "WFControlFlowMode": 0,
            "WFCondition": 1,   # Less Than
            "WFNumberValue": action_out(u_count_select, "count_select"),
            "WFInput": {
                "Type": "Variable",
                "Variable": repeat_index_ref()
            }
        }
    })

    # ── [30] Get url_media from api_result["medias"][label_now] ──────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.getvalueforkey",
        "WFWorkflowActionParameters": {
            "UUID": u_url_media,
            "CustomOutputName": "url_media",
            "WFDictionaryKey": text_tok("\ufffc", {
                "{0, 1}": {"VariableName": "label_now", "Type": "Variable"}
            }),
            "WFInput": var_ref("api_result", agg_dict_key("medias"))
        }
    })

    # ── [31] Set url_fetch = url_media (để vòng lặp sau tải) ─────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "url_fetch",
            "WFInput": action_out(u_url_media, "url_media")
        }
    })

    # ── [32] END IF Repeat Index < count ──────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_url_fetch_val,
            "WFControlFlowMode": 2
        }
    })

    # ── [33] IF url_fetch has any value ───────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_url_contains_op,
            "WFControlFlowMode": 0,
            "WFCondition": 100,
            "WFInput": {
                "Type": "Variable",
                "Variable": var_ref("url_fetch")
            }
        }
    })

    # ── [34] IF url_fetch contains {{open-url}} ───────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_open_url,
            "WFControlFlowMode": 0,
            "WFCondition": 99,   # contains
            "WFConditionalActionString": "{{open-url}}",
            "WFInput": {
                "Type": "Variable",
                "Variable": var_ref("url_fetch")
            }
        }
    })

    # ── [35] Get Text (replace {{open-url}}) ──────────────────────────────────
    _u_openurl_text = uid()
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
        "WFWorkflowActionParameters": {
            "UUID": _u_openurl_text,
            "WFTextActionText": text_tok("\ufffc", {
                "{0, 1}": {"VariableName": "url_fetch", "Type": "Variable"}
            })
        }
    })

    # ── [36] Exit (sau khi open-url) ──────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.exit",
        "WFWorkflowActionParameters": {}
    })

    # ── [37] END IF open-url ──────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_open_url,
            "WFControlFlowMode": 2
        }
    })

    # ── [38] ELSE (url_fetch không có giá trị) ────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_url_contains_op,
            "WFControlFlowMode": 1
        }
    })

    # ── [39] IF url_fetch contains ... (ask user) ─────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_url_contains2,
            "WFControlFlowMode": 0,
            "WFCondition": 99,
            "WFConditionalActionString": "...",
            "WFInput": {
                "Type": "Variable",
                "Variable": var_ref("url_fetch")
            }
        }
    })

    # ── [40] Ask for Text (với default = url_fetch) ───────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.ask",
        "WFWorkflowActionParameters": {
            "WFAskActionPrompt": text_tok("\ufffc", {
                "{0, 1}": {"VariableName": "url_fetch", "Type": "Variable"}
            }),
            "WFAskActionDefaultAnswer": {
                "Value": {
                    "string": "\ufffc",
                    "attachmentsByRange": {"{0, 1}": {"Type": "Clipboard"}}
                },
                "WFSerializationType": "WFTextTokenString"
            },
            "WFAllowsMultilineText": False
        }
    })

    # ── [41] Get Text ─────────────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
        "WFWorkflowActionParameters": {
            "WFTextActionText": text_tok("\ufffc", {
                "{0, 1}": {"Type": "Clipboard"}
            })
        }
    })

    # ── [42] Exit ─────────────────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.exit",
        "WFWorkflowActionParameters": {}
    })

    # ── [43] END IF ask ───────────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_url_contains2,
            "WFControlFlowMode": 2
        }
    })

    # ── [44] END IF url_fetch has value ───────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_url_contains_op,
            "WFControlFlowMode": 2
        }
    })

    # ── [45] IF url_fetch contains {{open-url}} (second check, for download) ──
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_url_fetch_val2,
            "WFControlFlowMode": 0,
            "WFCondition": 99,
            "WFConditionalActionString": "{{open-url}}",
            "WFInput": {
                "Type": "Variable",
                "Variable": var_ref("url_fetch")
            }
        }
    })

    # ── [46] Replace {{open-url}} ─────────────────────────────────────────────
    _u_replaced = uid()
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.text.replace",
        "WFWorkflowActionParameters": {
            "UUID": _u_replaced,
            "CustomOutputName": "Updated Text",
            "WFReplaceTextFind": "{{open-url}}",
            "WFReplaceTextReplace": "",
            "WFInput": var_ref("url_fetch")
        }
    })

    # ── [47] IF Updated Text is not empty → Open URL ──────────────────────────
    _g_replace_check = uid()
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": _g_replace_check,
            "WFControlFlowMode": 0,
            "WFCondition": 5,   # Is not empty / is not anything
            "WFInput": {
                "Type": "Variable",
                "Variable": action_out(_u_replaced, "Updated Text")
            }
        }
    })

    # ── [48] Open URL ─────────────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.openurl",
        "WFWorkflowActionParameters": {
            "WFInput": action_out(_u_replaced, "Updated Text")
        }
    })

    # ── [49] END IF not empty ─────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": _g_replace_check,
            "WFControlFlowMode": 2
        }
    })

    # ── [50] Exit ─────────────────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.exit",
        "WFWorkflowActionParameters": {}
    })

    # ── [51] END IF url_fetch contains {{open-url}} ───────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_url_fetch_val2,
            "WFControlFlowMode": 2
        }
    })

    # ── [52] IF fetch_result (media download) has any value ───────────────────
    # Tải media từ url_fetch (= url_media)
    # Trước tiên cần tải file từ URL media
    _u_media_dl = uid()
    _u_url_text = uid()  # gettext để convert url_media → text string
    
    # [52] Get Text từ url_fetch → url_text_clean (fix iOS Get URL Content error)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
        "WFWorkflowActionParameters": {
            "UUID": _u_url_text,
            "CustomOutputName": "url_text",
            "WFTextActionText": text_tok("\ufffc", {
                "{0, 1}": {"VariableName": "url_fetch", "Type": "Variable"}
            })
        }
    })

    # [53] Download media từ url_text → fetch_result (media)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.downloadurl",
        "WFWorkflowActionParameters": {
            "UUID": _u_media_dl,
            "CustomOutputName": "fetch_result",
            "ShowHeaders": False,
            "WFURL": text_tok("\ufffc", {
                "{0, 1}": {
                    "OutputUUID": _u_url_text,
                    "OutputName": "url_text",
                    "Type": "ActionOutput",
                    "Aggrandizements": [agg_url()]
                }
            })
        }
    })

    # [54] IF fetch_result has value (tải thành công) ─────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_has_fetch,
            "WFControlFlowMode": 0,
            "WFCondition": 5,   # is not empty
            "WFInput": {
                "Type": "Variable",
                "Variable": action_out(_u_media_dl, "fetch_result")
            }
        }
    })

    # [55] Match extension trong label_now ────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.text.match",
        "WFWorkflowActionParameters": {
            "UUID": u_match_ext,
            "WFMatchTextPattern": "mp4|mov|jpg|jpeg|heic|png|webp|mp3|m4a",
            "WFMatchTextCaseSensitive": False,
            "text": text_tok("\ufffc", {
                "{0, 1}": {"VariableName": "label_now", "Type": "Variable"}
            })
        }
    })

    # [56] Change case → ext ──────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.text.changecase",
        "WFWorkflowActionParameters": {
            "UUID": u_ext,
            "CustomOutputName": "ext",
            "WFCaseType": "lowercase",
            "text": action_out(u_match_ext, "Kết quả")
        }
    })

    # [57] Random number 1-9999999 ────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.number.random",
        "WFWorkflowActionParameters": {
            "UUID": u_rand_num,
            "WFRandomNumberMinimum": "1",
            "WFRandomNumberMaximum": "9999999"
        }
    })

    # [58] Set Name: snapall--[title]-[rand].[ext]
    # String: "snapall--\ufffc-\ufffc.\ufffc"
    # prefix "snapall--" = 9 chars
    # {9,1}=title, {11,1}=rand, {13,1}=ext  (dấu "-" thay vì " - ")
    prefix = f"{shortcut_name.lower().replace(' ', '')}--"
    p = len(prefix)
    name_str = f"{prefix}\ufffc-\ufffc.\ufffc"
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setitemname",
        "WFWorkflowActionParameters": {
            "UUID": u_media_loaded,
            "CustomOutputName": "media_loaded",
            "WFName": text_tok(name_str, {
                f"{{{p}, 1}}":   {"VariableName": "api_result", "Type": "Variable", "Aggrandizements": agg_dict_key("title")},
                f"{{{p+2}, 1}}": {"OutputUUID": u_rand_num, "OutputName": "Số ngẫu nhiên", "Type": "ActionOutput"},
                f"{{{p+4}, 1}}": {"OutputUUID": u_ext, "OutputName": "ext", "Type": "ActionOutput"}
            }),
            "WFInput": action_out(_u_media_dl, "fetch_result")
        }
    })

    # [59] IF label_now contains 🎵 → lưu Documents ───────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_is_audio,
            "WFControlFlowMode": 0,
            "WFCondition": 99,
            "WFConditionalActionString": "🎵",
            "WFInput": {
                "Type": "Variable",
                "Variable": var_ref("label_now", [agg_str()])
            }
        }
    })

    # [60] Save to Documents ─────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.documentpicker.save",
        "WFWorkflowActionParameters": {
            "UUID": u_saved_file,
            "WFAskWhereToSave": False,
            "WFInput": action_out(u_media_loaded, "media_loaded")
        }
    })

    # [61] Set m_file = api_result["open_file"] ───────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "m_file",
            "WFInput": var_ref("api_result", agg_dict_key("open_file"))
        }
    })

    # [62] OTHERWISE ──────────────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_is_audio,
            "WFControlFlowMode": 1
        }
    })

    # [63] Save to Photos/Recents ─────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.savetocameraroll",
        "WFWorkflowActionParameters": {
            "WFInput": action_out(u_media_loaded, "media_loaded")
        }
    })

    # [64] Set m_album = api_result["open_album"] ─────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "m_album",
            "WFInput": var_ref("api_result", agg_dict_key("open_album"))
        }
    })

    # [65] END IF is_audio ────────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_is_audio,
            "WFControlFlowMode": 2
        }
    })

    # [66] END IF has_fetch ───────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_has_fetch,
            "WFControlFlowMode": 2
        }
    })

    # ── PHẦN 3: MENU SAU KHI TẢI XONG ────────────────────────────────────────
    # [67] IF Repeat Index > count_select → hiện menu xong ────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "UUID": uid(),
            "GroupingIdentifier": g_loop_done,
            "WFControlFlowMode": 0,
            "WFCondition": 2,   # Greater Than
            "WFNumberValue": action_out(u_count_select, "count_select"),
            "WFInput": {
                "Type": "Variable",
                "Variable": repeat_index_ref()
            }
        }
    })

    # [68] Add m_album to menu_done ───────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.appendvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "menu_done",
            "WFInput": var_ref("m_album")
        }
    })

    # [69] Add m_file to menu_done ────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.appendvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "menu_done",
            "WFInput": var_ref("m_file")
        }
    })

    # [70] Add close to menu_done ─────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.appendvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "menu_done",
            "WFInput": var_ref("api_result", agg_dict_key("close"))
        }
    })

    # [71] Choose from menu_done ──────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefromlist",
        "WFWorkflowActionParameters": {
            "UUID": u_menu_select,
            "CustomOutputName": "menu_done_select",
            "WFInput": var_ref("menu_done"),
            "WFChooseFromListActionPrompt": text_tok("\ufffc", {
                "{0, 1}": var_ref("api_result", agg_dict_key("menu_done_title"))["Value"]
            }),
            "WFChooseFromListActionSelectMultiple": False
        }
    })

    # [72] IF menu_done_select == open_album ──────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "UUID": uid(),
            "GroupingIdentifier": g_open_album,
            "WFControlFlowMode": 0,
            "WFCondition": 4,
            "WFInput": {
                "Type": "Variable",
                "Variable": action_out(u_menu_select, "menu_done_select", [agg_str()])
            },
            "WFConditionalActionString": text_tok("\ufffc", {
                "{0, 1}": var_ref("api_result", agg_dict_key("open_album"))["Value"]
            })
        }
    })

    # [73] Open Photos ────────────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.openapp",
        "WFWorkflowActionParameters": {
            "WFAppIdentifier": "com.apple.mobileslideshow",
            "WFSelectedApp": {
                "BundleIdentifier": "com.apple.Photos",
                "Name": "Photos",
                "TeamIdentifier": "0000000000"
            }
        }
    })

    # [74] END IF open_album ──────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_open_album,
            "WFControlFlowMode": 2
        }
    })

    # [75] IF menu_done_select == open_file ───────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "UUID": uid(),
            "GroupingIdentifier": g_open_file,
            "WFControlFlowMode": 0,
            "WFCondition": 4,
            "WFInput": {
                "Type": "Variable",
                "Variable": action_out(u_menu_select, "menu_done_select", [agg_str()])
            },
            "WFConditionalActionString": text_tok("\ufffc", {
                "{0, 1}": var_ref("api_result", agg_dict_key("open_file"))["Value"]
            })
        }
    })

    # [76] Open in Files (Saved File) ─────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.openin",
        "WFWorkflowActionParameters": {
            "WFOpenInAppIdentifier": "com.apple.DocumentsApp",
            "WFOpenInAskWhenRun": False,
            "WFInput": action_out(u_saved_file, "Tệp đã lưu")
        }
    })

    # [77] END IF open_file ───────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_open_file,
            "WFControlFlowMode": 2
        }
    })

    # [78] Exit (kết thúc shortcut) ───────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.exit",
        "WFWorkflowActionParameters": {}
    })

    # [79] END IF loop_done ───────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_loop_done,
            "WFControlFlowMode": 2
        }
    })

    # [80] END REPEAT ─────────────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.repeat.count",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_repeat,
            "WFControlFlowMode": 2
        }
    })

    all_content_classes = [
        "WFAppStoreAppContentItem", "WFArticleContentItem", "WFContactContentItem",
        "WFDateContentItem", "WFEmailAddressContentItem", "WFGenericFileContentItem",
        "WFImageContentItem", "WFiTunesProductContentItem", "WFLocationContentItem",
        "WFDCMapsLinkContentItem", "WFAVAssetContentItem", "WFPDFContentItem",
        "WFPhoneNumberContentItem", "WFRichTextContentItem", "WFSafariWebPageContentItem",
        "WFStringContentItem", "WFURLContentItem"
    ]

    return {
        "WFWorkflowMinimumClientVersion": 900,
        "WFWorkflowClientVersion": "2607.1",
        "WFWorkflowClientRelease": "9.0",
        "WFWorkflowIcon": {
            "WFWorkflowIconStartColor": 4282601983,
            "WFWorkflowIconGlyphNumber": 59511
        },
        "WFWorkflowTypes": ["NCWidget", "ActionExtension", "QuickLook"],
        "WFWorkflowInputContentItemClasses": all_content_classes,
        "WFWorkflowActions": A
    }


def generate_shortcut(source_file, signed_file, api_url, name):
    wf = build_workflow(api_url=api_url, shortcut_name=name)
    with open(source_file, "wb") as f:
        plistlib.dump(wf, f)
    print(f"📦 Source: {source_file} ({len(wf['WFWorkflowActions'])} actions)")
    try:
        subprocess.run(
            ["shortcuts", "sign", "--mode", "anyone", "--input", source_file, "--output", signed_file],
            check=True
        )
        print(f"✅ Signed: {signed_file} ({os.path.getsize(signed_file)} bytes)")
    except Exception as e:
        print(f"⚠️  Ký số thất bại: {e}")


if __name__ == "__main__":
    generate_shortcut("SnapAll_Source.shortcut", "SnapAll.shortcut", DEFAULT_API_URL, "SnapAll")
    generate_shortcut("SnapVideo_Source.shortcut", "SnapVideo.shortcut", DEFAULT_API_URL, "Snap Video")
