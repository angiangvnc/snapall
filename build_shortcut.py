#!/usr/bin/env python3
"""
SnapAll v10.0 – Clone 1:1 toàn bộ 87 actions của Snap Video thực tế.
Chỉ thay:
  - API URL: phimtat.vn → snapall.vercel.app
  - runworkflow name: "Snap Video" → shortcut_name (SnapAll)
  - data:text/html script: giữ nguyên cấu trúc, chỉ thay URL redirect

Cách hoạt động (giống hệt Snap Video):
  1. Base64 encode input URL
  2. Chạy data:text/html script để parse config JSON → main_json
  3. URL Decode kết quả → dictionary
  4. Set main_json = dictionary
  5. Build API URL: snapall.vercel.app/api/parse?b64=...&lang=...&...
  6. Set url_fetch = API URL
  7. REPEAT 100:
     a. Base64 encode url_fetch
     b. Build download URL: url_fetch["url_red"] + b64(url_fetch)
     c. Get URL Content → fetch_result (JSON hoặc file)
     d. IF ext == "json" → IF reload → RunWorkflow(self) + exit
     e. IF Repeat Index == 1 (lần đầu) → parse API response → chọn định dạng
     f. Get item từ selected_item theo Repeat Index → label_now
     g. IF Repeat < count → get url_media → set url_fetch
     h. IF url_fetch has value AND contains {{open-url}} → open URL + exit
     i. IF url_fetch has value ELSE → IF contains "💬" → Ask + RunWorkflow(self) + exit
     j. IF url_fetch contains {{open-url}} → Replace + open URL + exit
     k. IF fetch_result has value → match ext → random → setitemname
     l. IF audio → save Documents; ELSE → save Photos
     m. IF Repeat > count → menu xong (appendvariable → choosefromlist → openapp/openin)
"""

import plistlib
import os
import uuid
import subprocess

API_URL = "https://snapall.vercel.app/api/parse"
API_RED64 = "https://snapall.vercel.app/api/parse?b64="


def uid():
    return str(uuid.uuid4()).upper()


def act_out(output_uuid, output_name, aggrandizements=None):
    val = {"OutputUUID": output_uuid, "OutputName": output_name, "Type": "ActionOutput"}
    if aggrandizements:
        val["Aggrandizements"] = aggrandizements
    return {"Value": val, "WFSerializationType": "WFTextTokenAttachment"}


def var_ref(name, aggrandizements=None):
    val = {"VariableName": name, "Type": "Variable"}
    if aggrandizements:
        val["Aggrandizements"] = aggrandizements
    return {"Value": val, "WFSerializationType": "WFTextTokenAttachment"}


def repeat_idx():
    return {"Value": {"VariableName": "Repeat Index", "Type": "Variable"}, "WFSerializationType": "WFTextTokenAttachment"}


def tok(s, att=None):
    v = {"string": s}
    if att:
        v["attachmentsByRange"] = att
    return {"Value": v, "WFSerializationType": "WFTextTokenString"}


def agg_str():
    return {"Type": "WFCoercionVariableAggrandizement", "CoercionItemClass": "WFStringContentItem"}


def agg_url():
    return {"Type": "WFCoercionVariableAggrandizement", "CoercionItemClass": "WFURLContentItem"}


def agg_rich():
    return {"Type": "WFCoercionVariableAggrandizement", "CoercionItemClass": "WFRichTextContentItem"}


def agg_dict():
    return {"Type": "WFCoercionVariableAggrandizement", "CoercionItemClass": "WFDictionaryContentItem"}


def agg_dict_key(key):
    return [agg_dict(), {"Type": "WFDictionaryValueVariableAggrandizement", "DictionaryKey": key}]


def build_workflow(shortcut_name="SnapAll"):
    A = []

    # ─── UUIDs ───────────────────────────────────────────────────────────────
    u_setting         = uid()
    u_b64_input       = uid()   # [3] base64encode input
    u_data_url        = uid()   # [4] data:text/html URL
    u_urldecode       = uid()   # [5] urlencode (decode mode)
    u_api_url         = uid()   # [7] API URL action
    u_api_url_var     = uid()   # UUID of setvariable url_fetch

    # Inside loop
    u_b64_loop        = uid()   # [10] base64encode url_fetch
    u_dl_url          = uid()   # [11] URL action: url_red + b64
    u_fetch_result    = uid()   # [12] downloadurl → fetch_result

    # runworkflow (self-call)
    u_rw1             = uid()   # [15] runworkflow (reload)
    u_rw2             = uid()   # [42] runworkflow (open-url)
    u_rw3             = uid()   # [49] runworkflow (ask input)

    # gettext/ask inside loop
    u_gettext_openurl = uid()   # [41] gettext for open-url
    u_ask             = uid()   # [47] ask
    u_gettext_ask     = uid()   # [48] gettext combining input + ask result

    # selected_item / label
    u_item_list       = uid()   # getitemfromlist → Mục từ danh sách
    u_count_select    = uid()   # count
    u_url_media       = uid()   # getvalueforkey → url_media

    # Download media
    u_url_text        = uid()   # gettext → url_text (fix iOS)
    u_media_dl        = uid()   # downloadurl → fetch_result (media)

    # File naming
    u_match_ext       = uid()
    u_ext             = uid()
    u_rand_num        = uid()
    u_media_loaded    = uid()

    # Save
    u_saved_file      = uid()   # documentpicker.save

    # Menu
    u_menu_select     = uid()   # choosefromlist → menu_done_select

    # Group IDs
    g_repeat          = uid()
    g_fetch_is_json   = uid()
    g_reload          = uid()
    g_url_is_1        = uid()
    g_skip_select     = uid()
    g_select_multiple = uid()
    g_skip_if_end     = uid()
    g_lt_count        = uid()
    g_has_url_fetch   = uid()
    g_open_url1       = uid()
    g_else_url        = uid()
    g_chat_url        = uid()
    g_open_url2       = uid()
    g_open_url2b      = uid()
    g_has_fetch       = uid()
    g_is_audio        = uid()
    g_loop_done       = uid()
    g_open_album      = uid()
    g_open_file       = uid()

    # ─── [0] Comment ─────────────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.comment",
        "WFWorkflowActionParameters": {
            "WFCommentActionText": (
                f"⚡️ {shortcut_name} v10.0\n"
                "Clone 1:1 cấu trúc Snap Video thực tế (87 actions).\n"
                f"API: {API_URL}"
            )
        }
    })

    # ─── [1] Dictionary: setting ──────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.dictionary",
        "WFWorkflowActionParameters": {
            "UUID": u_setting,
            "CustomOutputName": "setting",
            "WFItems": {
                "Value": {
                    "WFDictionaryFieldValueItems": [
                        {"WFKey": tok("ask_format"), "WFItemType": 0, "WFValue": tok("")},
                        {"WFKey": tok("show_menu"),  "WFItemType": 0, "WFValue": tok("")},
                    ]
                },
                "WFSerializationType": "WFDictionaryFieldValue"
            }
        }
    })

    # ─── [2] Comment ─────────────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.comment",
        "WFWorkflowActionParameters": {"WFCommentActionText": "=== NHẬN URL + CONFIG ==="}
    })

    # ─── [3] Base64 encode input (giống hệt SV: coerce to String) ─────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.base64encode",
        "WFWorkflowActionParameters": {
            "UUID": u_b64_input,
            "WFBase64LineBreakMode": "None",
            "WFInput": {
                "Value": {
                    "Type": "ExtensionInput",
                    "Aggrandizements": [agg_str()]
                },
                "WFSerializationType": "WFTextTokenAttachment"
            }
        }
    })

    # ─── [4] URL action: data:text/html script (giống hệt Snap Video) ────────
    # Script parse config JSON, tính url64, lang → trả về JSON object
    # Chỉ thay URL API của riêng mình
    script = (
        "data:text/html,<script>"
        "var b64=`\ufffc`;"
        "var cfg=`\ufffc`;"
        "function b64decodeUnicode(str){"
        "try{return decodeURIComponent(escape(atob(str)));}"
        "catch(e){try{return atob(str);}catch(e2){return '';}}"
        "}"
        "var t=b64decodeUnicode(b64);"
        "var c=JSON.parse(cfg);"
        "var m=t.match(/https?:\\/\\/[^\\s]+/);"
        "var lang=(navigator.language||navigator.userLanguage||'').split('-')[0];"
        "var o={"
        f"url_red:\"{API_RED64}\","
        "url64:m?btoa(unescape(encodeURIComponent(m[0]))):\"\","
        "lang:lang,"
        "ask_format:String(c.ask_format),"
        "show_menu:String(c.show_menu),"
        "skip_update:t.indexOf('{{skip_update}}')>-1?'true':'false'"
        "};"
        "document.write(JSON.stringify(o));"
        "</script>"
    )
    # Tính offset trong script: "var b64=`" = 23 chars → b64 at 23
    # "var cfg=`" sau đó: 23+1+10 = ???
    # Cần tính chính xác
    prefix_b64 = "data:text/html,<script>var b64=`"
    offset_b64 = len(prefix_b64)  # 32
    prefix_cfg = prefix_b64 + "\ufffc`;var cfg=`"
    offset_cfg = len(prefix_cfg)   # 32+1+10 = 43

    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.url",
        "WFWorkflowActionParameters": {
            "UUID": u_data_url,
            "WFURLActionURL": tok(script, {
                f"{{{offset_b64}, 1}}": {
                    "OutputUUID": u_b64_input,
                    "OutputName": "Đã mã hóa Base64",
                    "Type": "ActionOutput"
                },
                f"{{{offset_cfg}, 1}}": {
                    "OutputUUID": u_setting,
                    "OutputName": "setting",
                    "Type": "ActionOutput"
                }
            })
        }
    })

    # ─── [5] URL Decode (decode mode): parse data:text/html → JSON string ────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.urlencode",
        "WFWorkflowActionParameters": {
            "UUID": u_urldecode,
            "WFEncodeMode": "Decode",
            "WFInput": tok("\ufffc", {
                "{0, 1}": {
                    "OutputUUID": u_data_url,
                    "OutputName": "URL",
                    "Type": "ActionOutput",
                    "Aggrandizements": [agg_rich()]
                }
            })
        }
    })

    # ─── [6] Set main_json = urldecode → coerce to Dictionary ────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "main_json",
            "WFInput": {
                "Value": {
                    "OutputUUID": u_urldecode,
                    "OutputName": "Văn bản URL đã giải mã",
                    "Type": "ActionOutput",
                    "Aggrandizements": [agg_dict()]
                },
                "WFSerializationType": "WFTextTokenAttachment"
            }
        }
    })

    # ─── [7] URL action: API URL với params (giống Snap Video, thay domain) ──
    # "https://snapall.vercel.app/api/parse?lang=\ufffc&b64=\ufffc"
    api_url_str = f"{API_URL}?lang=\ufffc&ask_format=\ufffc&show_menu=\ufffc&skip_update=\ufffc&b64=\ufffc"
    # Tính offsets:
    base = f"{API_URL}?lang="
    o_lang        = len(base)                   # offset of lang value
    o_ask_format  = o_lang + 1 + len("&ask_format=")
    o_show_menu   = o_ask_format + 1 + len("&show_menu=")
    o_skip_update = o_show_menu + 1 + len("&skip_update=")
    o_b64         = o_skip_update + 1 + len("&b64=")

    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.url",
        "WFWorkflowActionParameters": {
            "UUID": u_api_url,
            "WFURLActionURL": tok(api_url_str, {
                f"{{{o_lang}, 1}}":        var_ref("main_json", agg_dict_key("lang"))["Value"],
                f"{{{o_ask_format}, 1}}":  var_ref("main_json", agg_dict_key("ask_format"))["Value"],
                f"{{{o_show_menu}, 1}}":   var_ref("main_json", agg_dict_key("show_menu"))["Value"],
                f"{{{o_skip_update}, 1}}": var_ref("main_json", agg_dict_key("skip_update"))["Value"],
                f"{{{o_b64}, 1}}":         var_ref("main_json", agg_dict_key("url64"))["Value"],
            })
        }
    })

    # ─── [8] Set url_fetch = URL (action 7) ──────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "UUID": u_api_url_var,
            "WFVariableName": "url_fetch",
            "WFInput": act_out(u_api_url, "URL")
        }
    })

    # ─── [9] REPEAT 100 ──────────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.repeat.count",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_repeat,
            "WFControlFlowMode": 0,
            "WFRepeatCount": 100
        }
    })

    # ─── [10] Base64 encode url_fetch (coerce to String) ─────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.base64encode",
        "WFWorkflowActionParameters": {
            "UUID": u_b64_loop,
            "WFBase64LineBreakMode": "None",
            "WFInput": var_ref("url_fetch", [agg_str()])
        }
    })

    # ─── [11] URL action: url_red + b64(url_fetch) ───────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.url",
        "WFWorkflowActionParameters": {
            "UUID": u_dl_url,
            "WFURLActionURL": tok("\ufffc\ufffc", {
                "{0, 1}": var_ref("main_json", agg_dict_key("url_red"))["Value"],
                "{1, 1}": {
                    "OutputUUID": u_b64_loop,
                    "OutputName": "Đã mã hóa Base64",
                    "Type": "ActionOutput"
                }
            })
        }
    })

    # ─── [12] Get URL Content → fetch_result ─────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.downloadurl",
        "WFWorkflowActionParameters": {
            "UUID": u_fetch_result,
            "CustomOutputName": "fetch_result",
            "ShowHeaders": False,
            "WFHTTPHeaders": {
                "Value": {
                    "WFDictionaryFieldValueItems": [{
                        "WFKey": tok("User-Agent"),
                        "WFItemType": 0,
                        "WFValue": tok(f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36")
                    }]
                },
                "WFSerializationType": "WFDictionaryFieldValue"
            },
            "WFURL": tok("\ufffc", {
                "{0, 1}": {"OutputUUID": u_dl_url, "OutputName": "URL", "Type": "ActionOutput"}
            })
        }
    })

    # ─── [13] IF fetch_result.extension == "json" ────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_fetch_is_json,
            "WFControlFlowMode": 0,
            "WFCondition": 4,
            "WFConditionalActionString": "json",
            "WFInput": {
                "Type": "Variable",
                "Variable": act_out(u_fetch_result, "fetch_result", [
                    agg_dict(),
                    {"PropertyUserInfo": "WFFileExtensionProperty", "Type": "WFPropertyVariableAggrandizement", "PropertyName": "File Extension"}
                ])
            }
        }
    })

    # ─── [14] IF fetch_result["reload"] has value ────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_reload,
            "WFControlFlowMode": 0,
            "WFCondition": 100,
            "WFInput": {
                "Type": "Variable",
                "Variable": act_out(u_fetch_result, "fetch_result", agg_dict_key("reload"))
            }
        }
    })

    # ─── [15] RunWorkflow (self) với input = fetch_result["reload"] ───────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.runworkflow",
        "WFWorkflowActionParameters": {
            "UUID": u_rw1,
            "WFWorkflowName": shortcut_name,
            "WFWorkflow": {
                "workflowName": shortcut_name,
                "isSelf": True
            },
            "WFInput": act_out(u_fetch_result, "fetch_result", agg_dict_key("reload"))
        }
    })

    # ─── [16] Exit ───────────────────────────────────────────────────────────
    A.append({"WFWorkflowActionIdentifier": "is.workflow.actions.exit", "WFWorkflowActionParameters": {}})

    # ─── [17] END IF reload ──────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_reload, "WFControlFlowMode": 2}
    })

    # ─── [18] END IF fetch_is_json ───────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_fetch_is_json, "WFControlFlowMode": 2}
    })

    # ─── [19] IF Repeat Index == 1 ───────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_url_is_1,
            "WFControlFlowMode": 0,
            "WFCondition": 4,
            "WFNumberValue": "1",
            "WFInput": {"Type": "Variable", "Variable": repeat_idx()}
        }
    })

    # ─── [20] Set api_result = fetch_result ──────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "api_result",
            "WFInput": act_out(u_fetch_result, "fetch_result")
        }
    })

    # ─── [21] IF api_result["skip_select"] has value ─────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_skip_select,
            "WFControlFlowMode": 0,
            "WFCondition": 100,
            "WFInput": {"Type": "Variable", "Variable": var_ref("api_result", agg_dict_key("skip_select"))}
        }
    })

    # ─── [22] Set selected_item = api_result["labels"] (auto-select all) ─────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "selected_item",
            "WFInput": var_ref("api_result", agg_dict_key("labels"))
        }
    })

    # ─── [23] ELSE ───────────────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_skip_select, "WFControlFlowMode": 1}
    })

    # ─── [24] IF api_result["select_multiple"] has value ─────────────────────
    _u_sm = uid()
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "UUID": _u_sm,
            "GroupingIdentifier": g_select_multiple,
            "WFControlFlowMode": 0,
            "WFCondition": 100,
            "WFInput": {"Type": "Variable", "Variable": var_ref("api_result", agg_dict_key("select_multiple"))}
        }
    })

    # ─── [25] choosefromlist (multi) ─────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefromlist",
        "WFWorkflowActionParameters": {
            "WFInput": var_ref("api_result", agg_dict_key("labels")),
            "WFChooseFromListActionPrompt": tok("\ufffc", {
                "{0, 1}": act_out(u_fetch_result, "fetch_result", agg_dict_key("menu_title"))["Value"]
            }),
            "WFChooseFromListActionSelectMultiple": True,
            "WFChooseFromListActionSelectAll": True
        }
    })

    # ─── [26] ELSE ───────────────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_select_multiple, "WFControlFlowMode": 1}
    })

    # ─── [27] choosefromlist (single) ────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefromlist",
        "WFWorkflowActionParameters": {
            "WFInput": var_ref("api_result", agg_dict_key("labels")),
            "WFChooseFromListActionPrompt": tok("\ufffc", {
                "{0, 1}": act_out(u_fetch_result, "fetch_result", agg_dict_key("menu_title"))["Value"]
            }),
            "WFChooseFromListActionSelectMultiple": False
        }
    })

    # ─── [28] END IF select_multiple ─────────────────────────────────────────
    _u_sm_end = uid()
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "UUID": _u_sm_end,
            "GroupingIdentifier": g_select_multiple,
            "WFControlFlowMode": 2
        }
    })

    # ─── [29] END IF skip_select ─────────────────────────────────────────────
    _u_skip_end = uid()
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "UUID": _u_skip_end,
            "GroupingIdentifier": g_skip_select,
            "WFControlFlowMode": 2
        }
    })

    # ─── [30] Set selected_item = If Result ──────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "selected_item",
            "WFInput": act_out(_u_skip_end, "Nếu kết quả")
        }
    })

    # ─── [31] END IF Repeat Index == 1 ───────────────────────────────────────
    _u_idx1_end = uid()
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "UUID": _u_idx1_end,
            "GroupingIdentifier": g_url_is_1,
            "WFControlFlowMode": 2
        }
    })

    # ─── [32] Set label_now (= giữ nguyên tên biến, nhưng gán sau khi count) ───
    # Snap Video gốc: [32]=setvariable(label_now), [33]=count, [34]=IF LT, [35]=getitemfromlist
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "label_now",
            "WFInput": act_out(_u_idx1_end, "Mục từ danh sách")
        }
    })

    # ─── [33] Count selected_item → count_select ─────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.count",
        "WFWorkflowActionParameters": {
            "UUID": u_count_select,
            "CustomOutputName": "count_select",
            "WFCountType": "Items",
            "Input": var_ref("selected_item")
        }
    })

    # ─── [34] IF Repeat Index < count_select ─────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_lt_count,
            "WFControlFlowMode": 0,
            "WFCondition": 1,   # Less Than
            "WFNumberValue": act_out(u_count_select, "count_select"),
            "WFInput": {"Type": "Variable", "Variable": repeat_idx()}
        }
    })

    # ─── [35] getitemfromlist → label_now (Snap Video: item from selected_item) ──
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.getitemfromlist",
        "WFWorkflowActionParameters": {
            "UUID": u_item_list,
            "CustomOutputName": "Mục từ danh sách",
            "WFItemSpecifier": "Item At Index",
            "WFItemIndex": repeat_idx(),
            "WFInput": var_ref("selected_item")
        }
    })

    # ─── [36] getvalueforkey → url_media ────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.getvalueforkey",
        "WFWorkflowActionParameters": {
            "UUID": u_url_media,
            "CustomOutputName": "url_media",
            "WFDictionaryKey": tok("\ufffc", {
                "{0, 1}": {"VariableName": "label_now", "Type": "Variable"}
            }),
            "WFInput": var_ref("api_result", agg_dict_key("medias"))
        }
    })

    # ─── [37] Set url_fetch = url_media ──────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "url_fetch",
            "WFInput": act_out(u_url_media, "url_media")
        }
    })

    # ─── [37] END IF < count ─────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_lt_count, "WFControlFlowMode": 2}
    })

    # ─── [38] IF url_fetch has value ─────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_has_url_fetch,
            "WFControlFlowMode": 0,
            "WFCondition": 100,
            "WFInput": {"Type": "Variable", "Variable": var_ref("url_fetch")}
        }
    })

    # ─── [39] IF url_fetch contains {{open-url}} ─────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_open_url1,
            "WFControlFlowMode": 0,
            "WFCondition": 99,
            "WFConditionalActionString": "{{open-url}}",
            "WFInput": {"Type": "Variable", "Variable": var_ref("url_fetch")}
        }
    })

    # ─── [40] IF url_fetch contains {{open-url}} → gettext ───────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
        "WFWorkflowActionParameters": {
            "UUID": u_gettext_openurl,
            "WFTextActionText": tok("\ufffc", {
                "{0, 1}": {"VariableName": "url_fetch", "Type": "Variable"}
            })
        }
    })

    # ─── [41] END IF → RunWorkflow (self) với gettext result ─────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.runworkflow",
        "WFWorkflowActionParameters": {
            "UUID": u_rw2,
            "WFWorkflowName": shortcut_name,
            "WFWorkflow": {"workflowName": shortcut_name, "isSelf": True},
            "WFInput": act_out(u_gettext_openurl, "Văn bản")
        }
    })

    # ─── [42] Exit ───────────────────────────────────────────────────────────
    A.append({"WFWorkflowActionIdentifier": "is.workflow.actions.exit", "WFWorkflowActionParameters": {}})

    # ─── [43] END IF open-url ────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_open_url1, "WFControlFlowMode": 2}
    })

    # ─── [44] ELSE (url_fetch không có giá trị) ──────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_has_url_fetch, "WFControlFlowMode": 1}
    })

    # ─── [45] IF url_fetch contains 💬 (ask mode) ────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_chat_url,
            "WFControlFlowMode": 0,
            "WFCondition": 99,
            "WFConditionalActionString": "💬",
            "WFInput": {
                "Type": "Variable",
                "Variable": act_out(u_item_list, "Mục từ danh sách", [agg_str()])
            }
        }
    })

    # ─── [46] Ask for input ───────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.ask",
        "WFWorkflowActionParameters": {
            "UUID": u_ask,
            "WFAllowsMultilineText": True,
            "WFAskActionPrompt": tok("\ufffc", {
                "{0, 1}": {"VariableName": "url_fetch", "Type": "Variable"}
            }),
            "WFAskActionDefaultAnswer": tok("\ufffc", {
                "{0, 1}": {"Type": "Clipboard"}
            })
        }
    })

    # ─── [47] Get Text: ExtensionInput + Ask result ───────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
        "WFWorkflowActionParameters": {
            "UUID": u_gettext_ask,
            "WFTextActionText": tok("\ufffc\ufffc", {
                "{0, 1}": {"Type": "ExtensionInput"},
                "{1, 1}": {
                    "OutputUUID": u_ask,
                    "OutputName": "Đầu vào đã cung cấp",
                    "Type": "ActionOutput"
                }
            })
        }
    })

    # ─── [48] RunWorkflow (self) với gettext result ───────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.runworkflow",
        "WFWorkflowActionParameters": {
            "UUID": u_rw3,
            "WFWorkflowName": shortcut_name,
            "WFWorkflow": {"workflowName": shortcut_name, "isSelf": True},
            "WFInput": act_out(u_gettext_ask, "Văn bản")
        }
    })

    # ─── [49] Exit ───────────────────────────────────────────────────────────
    A.append({"WFWorkflowActionIdentifier": "is.workflow.actions.exit", "WFWorkflowActionParameters": {}})

    # ─── [50] END IF 💬 ──────────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_chat_url, "WFControlFlowMode": 2}
    })

    # ─── [51] END IF url_fetch has value ─────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_has_url_fetch, "WFControlFlowMode": 2}
    })

    # ─── [52] IF url_fetch contains {{open-url}} (lần 2) ────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_open_url2,
            "WFControlFlowMode": 0,
            "WFCondition": 99,
            "WFConditionalActionString": "{{open-url}}",
            "WFInput": {"Type": "Variable", "Variable": var_ref("url_fetch")}
        }
    })

    # ─── [53] Replace {{open-url}} với "" ────────────────────────────────────
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

    # ─── [54] IF Updated Text is not empty ───────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_open_url2b,
            "WFControlFlowMode": 0,
            "WFCondition": 5,
            "WFInput": {
                "Type": "Variable",
                "Variable": act_out(_u_replaced, "Updated Text")
            }
        }
    })

    # ─── [55] Open URL ────────────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.openurl",
        "WFWorkflowActionParameters": {
            "WFInput": act_out(_u_replaced, "Updated Text")
        }
    })

    # ─── [56] END IF not empty ───────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_open_url2b, "WFControlFlowMode": 2}
    })

    # ─── [57] Exit ───────────────────────────────────────────────────────────
    A.append({"WFWorkflowActionIdentifier": "is.workflow.actions.exit", "WFWorkflowActionParameters": {}})

    # ─── [58] END IF {{open-url}} lần 2 ─────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_open_url2, "WFControlFlowMode": 2}
    })

    # ─── [59] IF fetch_result (from loop download) is not empty ─────────────
    # Snap Video gốc: dùng trực tiếp fetch_result từ action [12] downloadurl
    # (không có gettext/downloadurl riêng cho media - chính fetch_result đã là file media)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_has_fetch,
            "WFControlFlowMode": 0,
            "WFCondition": 5,   # is not empty
            "WFInput": {"Type": "Variable", "Variable": act_out(u_fetch_result, "fetch_result")}
        }
    })

    # ─── [60] text.match extension ───────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.text.match",
        "WFWorkflowActionParameters": {
            "UUID": u_match_ext,
            "WFMatchTextPattern": "mp4|mov|jpg|jpeg|heic|png|webp|mp3|m4a",
            "WFMatchTextCaseSensitive": False,
            "text": tok("\ufffc", {"{0, 1}": {"VariableName": "label_now", "Type": "Variable"}})
        }
    })

    # ─── [61] text.changecase → ext ──────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.text.changecase",
        "WFWorkflowActionParameters": {
            "UUID": u_ext,
            "CustomOutputName": "ext",
            "WFCaseType": "lowercase",
            "text": act_out(u_match_ext, "Kết quả")
        }
    })

    # ─── [62] Random number ───────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.number.random",
        "WFWorkflowActionParameters": {
            "UUID": u_rand_num,
            "WFRandomNumberMinimum": "1",
            "WFRandomNumberMaximum": "9999999"
        }
    })

    # ─── [63] setitemname: snapall--[title]-[rand].[ext] ─────────────────────
    prefix = f"{shortcut_name.lower().replace(' ', '')}--"
    p = len(prefix)
    # "snapall--\ufffc-\ufffc.\ufffc" → title at p, rand at p+2, ext at p+4
    name_str = f"{prefix}\ufffc-\ufffc.\ufffc"
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setitemname",
        "WFWorkflowActionParameters": {
            "UUID": u_media_loaded,
            "CustomOutputName": "media_loaded",
            "WFName": tok(name_str, {
                f"{{{p}, 1}}":   var_ref("api_result", agg_dict_key("title"))["Value"],
                f"{{{p+2}, 1}}": {"OutputUUID": u_rand_num, "OutputName": "Số ngẫu nhiên", "Type": "ActionOutput"},
                f"{{{p+4}, 1}}": {"OutputUUID": u_ext, "OutputName": "ext", "Type": "ActionOutput"}
            }),
            "WFInput": act_out(u_media_dl, "fetch_result")
        }
    })

    # ─── [64] IF label_now contains 🎵 ───────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_is_audio,
            "WFControlFlowMode": 0,
            "WFCondition": 99,
            "WFConditionalActionString": "🎵",
            "WFInput": {"Type": "Variable", "Variable": var_ref("label_now", [agg_str()])}
        }
    })

    # ─── [65] documentpicker.save ────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.documentpicker.save",
        "WFWorkflowActionParameters": {
            "UUID": u_saved_file,
            "WFAskWhereToSave": False,
            "WFInput": act_out(u_media_loaded, "media_loaded"),
            "WFFolder": {
                "filename": "File Provider Storage",
                "displayName": "Documents"
            }
        }
    })

    # ─── [66] Set m_file = api_result["open_file"] ───────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "m_file",
            "WFInput": var_ref("api_result", agg_dict_key("open_file"))
        }
    })

    # ─── [67] OTHERWISE ──────────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_is_audio, "WFControlFlowMode": 1}
    })

    # ─── [68] savetocameraroll (giống Snap Video gốc: input = media_loaded) ──
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.savetocameraroll",
        "WFWorkflowActionParameters": {
            "UUID": uid(),
            "WFInput": act_out(u_media_loaded, "media_loaded")
        }
    })

    # ─── [69] Set m_album = api_result["open_album"] ─────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "m_album",
            "WFInput": var_ref("api_result", agg_dict_key("open_album"))
        }
    })

    # ─── [70] END IF audio ───────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_is_audio, "WFControlFlowMode": 2}
    })

    # ─── [71] END IF has_fetch ───────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_has_fetch, "WFControlFlowMode": 2}
    })

    # ─── [72] IF Repeat Index > count_select ─────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "UUID": uid(),
            "GroupingIdentifier": g_loop_done,
            "WFControlFlowMode": 0,
            "WFCondition": 2,   # Greater Than
            "WFNumberValue": act_out(u_count_select, "count_select"),
            "WFInput": {"Type": "Variable", "Variable": repeat_idx()}
        }
    })

    # ─── [73] appendvariable m_album ─────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.appendvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "menu_done",
            "WFInput": var_ref("m_album")
        }
    })

    # ─── [74] appendvariable m_file ──────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.appendvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "menu_done",
            "WFInput": var_ref("m_file")
        }
    })

    # ─── [75] appendvariable close ───────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.appendvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "menu_done",
            "WFInput": var_ref("api_result", agg_dict_key("close"))
        }
    })

    # ─── [76] choosefromlist → menu_done_select ───────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefromlist",
        "WFWorkflowActionParameters": {
            "UUID": u_menu_select,
            "CustomOutputName": "menu_done_select",
            "WFInput": var_ref("menu_done"),
            "WFChooseFromListActionPrompt": tok("\ufffc", {
                "{0, 1}": var_ref("api_result", agg_dict_key("menu_done_title"))["Value"]
            }),
            "WFChooseFromListActionSelectMultiple": False
        }
    })

    # ─── [77] IF menu_done_select == open_album ───────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "UUID": uid(),
            "GroupingIdentifier": g_open_album,
            "WFControlFlowMode": 0,
            "WFCondition": 4,
            "WFInput": {
                "Type": "Variable",
                "Variable": act_out(u_menu_select, "menu_done_select", [agg_str()])
            },
            "WFConditionalActionString": tok("\ufffc", {
                "{0, 1}": var_ref("api_result", agg_dict_key("open_album"))["Value"]
            })
        }
    })

    # ─── [78] Open Photos ─────────────────────────────────────────────────────
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

    # ─── [79] END IF album ────────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_open_album, "WFControlFlowMode": 2}
    })

    # ─── [80] IF menu_done_select == open_file ────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "UUID": uid(),
            "GroupingIdentifier": g_open_file,
            "WFControlFlowMode": 0,
            "WFCondition": 4,
            "WFInput": {
                "Type": "Variable",
                "Variable": act_out(u_menu_select, "menu_done_select", [agg_str()])
            },
            "WFConditionalActionString": tok("\ufffc", {
                "{0, 1}": var_ref("api_result", agg_dict_key("open_file"))["Value"]
            })
        }
    })

    # ─── [81] Open in Files ───────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.openin",
        "WFWorkflowActionParameters": {
            "WFOpenInAppIdentifier": "com.apple.DocumentsApp",
            "WFOpenInAskWhenRun": False,
            "WFInput": act_out(u_saved_file, "Tệp đã lưu")
        }
    })

    # ─── [82] END IF file ────────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_open_file, "WFControlFlowMode": 2}
    })

    # ─── [83] Exit ───────────────────────────────────────────────────────────
    A.append({"WFWorkflowActionIdentifier": "is.workflow.actions.exit", "WFWorkflowActionParameters": {}})

    # ─── [84] END IF loop_done ───────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_loop_done, "WFControlFlowMode": 2}
    })

    # ─── [85] END REPEAT ─────────────────────────────────────────────────────
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.repeat.count",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_repeat, "WFControlFlowMode": 2}
    })

    all_content_classes = [
        "WFAppStoreAppContentItem", "WFArticleContentItem", "WFContactContentItem",
        "WFDateContentItem", "WFEmailAddressContentItem", "WFGenericFileContentItem",
        "WFImageContentItem", "WFiTunesProductContentItem", "WFLocationContentItem",
        "WFDCMapsLinkContentItem", "WFAVAssetContentItem", "WFPDFContentItem",
        "WFPhoneNumberContentItem", "WFRichTextContentItem", "WFSafariWebPageContentItem",
        "WFStringContentItem", "WFURLContentItem"
    ]

    print(f"  Total actions built: {len(A)} (Snap Video gốc: 87)")

    return {
        "WFWorkflowMinimumClientVersion": 900,
        "WFWorkflowClientVersion": "2607.1",
        "WFWorkflowClientRelease": "10.0",
        "WFWorkflowIcon": {
            "WFWorkflowIconStartColor": 4282601983,
            "WFWorkflowIconGlyphNumber": 59511
        },
        "WFWorkflowTypes": ["NCWidget", "ActionExtension", "QuickLook"],
        "WFWorkflowInputContentItemClasses": all_content_classes,
        "WFWorkflowActions": A
    }


def generate(source, signed, name):
    wf = build_workflow(shortcut_name=name)
    with open(source, "wb") as f:
        plistlib.dump(wf, f)
    print(f"📦 {source}")
    try:
        subprocess.run(
            ["shortcuts", "sign", "--mode", "anyone", "--input", source, "--output", signed],
            check=True
        )
        print(f"✅ {signed} ({os.path.getsize(signed):,} bytes)")
    except Exception as e:
        print(f"⚠️  Sign failed: {e}")


if __name__ == "__main__":
    generate("SnapAll_Source.shortcut", "SnapAll.shortcut", "SnapAll")
    generate("SnapVideo_Source.shortcut", "SnapVideo.shortcut", "Snap Video")
