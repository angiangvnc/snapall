#!/usr/bin/env python3
"""
SnapAll v11.3
- Fix WFControlFlowMode: 1 cho các nhánh menu choosefrommenu (fix crash "There was a problem running the shortcut SnapAll")
- Fix lưu api_json vào biến bằng setvariable sau downloadurl
- Fix b64 CustomOutputName độc lập ngôn ngữ
- Fix savetocameraroll mặc định chuẩn đa ngôn ngữ
- Kiểm tra an toàn shared_url trước khi gọi API
- Tự động audit cấu trúc AST shortcut trước khi ký số
"""

import plistlib
import os
import sys
import uuid
import subprocess

API_URL = "https://snapall.vercel.app/api/parse"


def uid():
    return str(uuid.uuid4()).upper()


def tok(s, att=None):
    v = {"string": s}
    if att:
        v["attachmentsByRange"] = att
    return {"Value": v, "WFSerializationType": "WFTextTokenString"}


def var_ref(name, aggrandizements=None):
    val = {"VariableName": name, "Type": "Variable"}
    if aggrandizements:
        val["Aggrandizements"] = aggrandizements
    return {"Value": val, "WFSerializationType": "WFTextTokenAttachment"}


def act_out(output_uuid, output_name, aggrandizements=None):
    val = {"OutputUUID": output_uuid, "OutputName": output_name, "Type": "ActionOutput"}
    if aggrandizements:
        val["Aggrandizements"] = aggrandizements
    return {"Value": val, "WFSerializationType": "WFTextTokenAttachment"}


def agg_str():
    return {"Type": "WFCoercionVariableAggrandizement", "CoercionItemClass": "WFStringContentItem"}


def agg_url():
    return {"Type": "WFCoercionVariableAggrandizement", "CoercionItemClass": "WFURLContentItem"}


def agg_dict():
    return {"Type": "WFCoercionVariableAggrandizement", "CoercionItemClass": "WFDictionaryContentItem"}


def agg_dict_key(key):
    return [agg_dict(), {"Type": "WFDictionaryValueVariableAggrandizement", "DictionaryKey": key}]


def UA():
    return "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"


def build_workflow(shortcut_name="SnapAll"):
    A = []

    # ─── UUIDs ───────────────────────────────────────────────────────────────
    u_ask_url       = uid()
    u_b64           = uid()
    u_api_url       = uid()
    u_api_json      = uid()
    u_selected      = uid()
    u_media_url_act = uid()
    u_media_file    = uid()

    # Group IDs
    g_no_input  = uid()
    g_menu      = uid()
    g_no_url    = uid()
    g_api_err   = uid()
    g_no_sel    = uid()
    g_each      = uid()
    g_is_audio  = uid()

    MENU_ENTER = "💬 Enter video link"
    MENU_GUIDE = "📖 User guide"
    MENU_SHARE = "⚠️ Not showing in the share sheet?"
    MENU_HIDE  = "⚙️ Hide this menu next time"

    # =========================================================================
    # PHASE 1: LẤY URL (Share Sheet hoặc Menu nhập tay)
    # =========================================================================

    # [0] IF Shortcut Input does not have any value (chạy trực tiếp không qua Share Sheet)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_no_input,
            "WFControlFlowMode": 0,
            "WFCondition": 101,   # Does not have a value
            "WFInput": {
                "Type": "Variable",
                "Variable": {
                    "Value": {"Type": "ExtensionInput"},
                    "WFSerializationType": "WFTextTokenAttachment"
                }
            }
        }
    })

    # [1] choosefrommenu "Choose an action" (WFControlFlowMode: 0 = Start Menu)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefrommenu",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_menu,
            "WFControlFlowMode": 0,
            "WFMenuPrompt": tok("Choose an action"),
            "WFMenuItems": [MENU_ENTER, MENU_GUIDE, MENU_SHARE, MENU_HIDE]
        }
    })

    # [2] CASE 1: Enter video link (WFControlFlowMode: 1 = Case Branch)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefrommenu",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_menu,
            "WFControlFlowMode": 1,
            "WFMenuItemTitle": MENU_ENTER
        }
    })
    # [3] Ask for URL
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.ask",
        "WFWorkflowActionParameters": {
            "UUID": u_ask_url,
            "WFAskActionPrompt": tok("💬 Nhập link video (TikTok, Facebook, ...):"),
            "WFAskActionDefaultAnswer": tok(""),
            "WFAskActionKeyboardType": "URL"
        }
    })
    # [4] Set shared_url = entered URL
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "shared_url",
            "WFInput": act_out(u_ask_url, "Provided Input")
        }
    })

    # [5] CASE 2: User guide (WFControlFlowMode: 1 = Case Branch)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefrommenu",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_menu,
            "WFControlFlowMode": 1,
            "WFMenuItemTitle": MENU_GUIDE
        }
    })
    # [6] Open guide web
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.openurl",
        "WFWorkflowActionParameters": {"WFURL": tok("https://snapall.vercel.app/")}
    })
    # [7] Exit
    A.append({"WFWorkflowActionIdentifier": "is.workflow.actions.exit", "WFWorkflowActionParameters": {}})

    # [8] CASE 3: Not showing in share sheet? (WFControlFlowMode: 1 = Case Branch)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefrommenu",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_menu,
            "WFControlFlowMode": 1,
            "WFMenuItemTitle": MENU_SHARE
        }
    })
    # [9] Open Apple help
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.openurl",
        "WFWorkflowActionParameters": {"WFURL": tok("https://support.apple.com/guide/shortcuts/use-shortcuts-in-apps-apd886daaaf3/ios")}
    })
    # [10] Exit
    A.append({"WFWorkflowActionIdentifier": "is.workflow.actions.exit", "WFWorkflowActionParameters": {}})

    # [11] CASE 4: Hide this menu next time (WFControlFlowMode: 1 = Case Branch)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefrommenu",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_menu,
            "WFControlFlowMode": 1,
            "WFMenuItemTitle": MENU_HIDE
        }
    })
    # [12] Exit
    A.append({"WFWorkflowActionIdentifier": "is.workflow.actions.exit", "WFWorkflowActionParameters": {}})

    # [13] END choosefrommenu (WFControlFlowMode: 2 = End Menu)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefrommenu",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_menu, "WFControlFlowMode": 2}
    })

    # [14] ELSE: có ExtensionInput từ Share Sheet (WFControlFlowMode: 1 = Else Branch)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_no_input, "WFControlFlowMode": 1}
    })
    # [15] Set shared_url = ExtensionInput (coerce to String)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "shared_url",
            "WFInput": {
                "Value": {"Type": "ExtensionInput", "Aggrandizements": [agg_str()]},
                "WFSerializationType": "WFTextTokenAttachment"
            }
        }
    })

    # [16] END IF no_input (WFControlFlowMode: 2 = End If)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_no_input, "WFControlFlowMode": 2}
    })

    # [17] Kiểm tra an toàn: nếu shared_url không có giá trị (bấm Cancel khi nhập) → Exit
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_no_url,
            "WFControlFlowMode": 0,
            "WFCondition": 101,  # Does not have a value
            "WFInput": {"Type": "Variable", "Variable": var_ref("shared_url", [agg_str()])}
        }
    })
    A.append({"WFWorkflowActionIdentifier": "is.workflow.actions.exit", "WFWorkflowActionParameters": {}})
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_no_url, "WFControlFlowMode": 2}
    })

    # =========================================================================
    # PHASE 2: GỌI API → PARSE JSON
    # =========================================================================

    # [18] base64encode(shared_url) → b64
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.base64encode",
        "WFWorkflowActionParameters": {
            "UUID": u_b64,
            "CustomOutputName": "b64",
            "WFBase64LineBreakMode": "None",
            "WFInput": var_ref("shared_url", [agg_str()])
        }
    })

    # [19] URL: API_URL?b64={b64} → api_url
    api_str = f"{API_URL}?b64=\ufffc"
    o_b64 = len(f"{API_URL}?b64=")
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.url",
        "WFWorkflowActionParameters": {
            "UUID": u_api_url,
            "CustomOutputName": "api_url",
            "WFURLActionURL": tok(api_str, {
                f"{{{o_b64}, 1}}": {
                    "OutputUUID": u_b64,
                    "OutputName": "b64",
                    "Type": "ActionOutput"
                }
            })
        }
    })

    # [20] downloadurl(api_url) → api_json_raw
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.downloadurl",
        "WFWorkflowActionParameters": {
            "UUID": u_api_json,
            "CustomOutputName": "api_json_raw",
            "ShowHeaders": False,
            "WFHTTPMethod": "GET",
            "WFURL": tok("\ufffc", {
                "{0, 1}": {
                    "OutputUUID": u_api_url,
                    "OutputName": "api_url",
                    "Type": "ActionOutput",
                    "Aggrandizements": [agg_url()]
                }
            }),
            "WFHTTPHeaders": {
                "Value": {
                    "WFDictionaryFieldValueItems": [{
                        "WFKey": tok("User-Agent"),
                        "WFItemType": 0,
                        "WFValue": tok(UA())
                    }]
                },
                "WFSerializationType": "WFDictionaryFieldValue"
            }
        }
    })

    # [21] Lưu kết quả API vào biến api_json (CỰC KỲ QUAN TRỌNG: để các lệnh sau đọc được dict)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "api_json",
            "WFInput": act_out(u_api_json, "api_json_raw")
        }
    })

    # =========================================================================
    # PHASE 3: KIỂM TRA LỖI API & CHỌN ĐỊNH DẠNG (HD / SD / MP3 / PHOTOS)
    # =========================================================================

    # [22] IF api_json["status"] == "error" → báo lỗi + exit
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_api_err,
            "WFControlFlowMode": 0,
            "WFCondition": 4,   # Is equal to
            "WFConditionalActionString": "error",
            "WFInput": {
                "Type": "Variable",
                "Variable": var_ref("api_json", [agg_dict(), {"Type": "WFDictionaryValueVariableAggrandizement", "DictionaryKey": "status"}, agg_str()])
            }
        }
    })
    # [23] Show error message
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.showresult",
        "WFWorkflowActionParameters": {
            "Text": tok("❌ \ufffc", {
                "{2, 1}": {
                    "VariableName": "api_json",
                    "Type": "Variable",
                    "Aggrandizements": [agg_dict(), {"Type": "WFDictionaryValueVariableAggrandizement", "DictionaryKey": "message"}, agg_str()]
                }
            })
        }
    })
    # [24] Exit
    A.append({"WFWorkflowActionIdentifier": "is.workflow.actions.exit", "WFWorkflowActionParameters": {}})

    # [25] END IF api_err
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_api_err, "WFControlFlowMode": 2}
    })

    # [26] Set medias = api_json["medias"] (Dictionary mapping nhãn → download link)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "medias",
            "WFInput": var_ref("api_json", agg_dict_key("medias"))
        }
    })

    # [27] choosefromlist: Hiện danh sách labels cho user chọn (HD / MP3 / ...)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefromlist",
        "WFWorkflowActionParameters": {
            "UUID": u_selected,
            "CustomOutputName": "selected",
            "WFChooseFromListActionPrompt": tok("\ufffc", {
                "{0, 1}": {
                    "VariableName": "api_json",
                    "Type": "Variable",
                    "Aggrandizements": [agg_dict(), {"Type": "WFDictionaryValueVariableAggrandizement", "DictionaryKey": "menu_title"}, agg_str()]
                }
            }),
            "WFChooseFromListActionSelectMultiple": True,
            "WFChooseFromListActionSelectAll": False,
            "WFInput": var_ref("api_json", agg_dict_key("labels"))
        }
    })

    # [28] Lưu mục đã chọn vào biến selected
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "selected",
            "WFInput": act_out(u_selected, "selected")
        }
    })

    # [29] IF selected không có giá trị (người dùng bấm Cancel) → Exit
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_no_sel,
            "WFControlFlowMode": 0,
            "WFCondition": 101,   # Does not have a value
            "WFInput": {"Type": "Variable", "Variable": var_ref("selected")}
        }
    })
    A.append({"WFWorkflowActionIdentifier": "is.workflow.actions.exit", "WFWorkflowActionParameters": {}})
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_no_sel, "WFControlFlowMode": 2}
    })

    # =========================================================================
    # PHASE 4: TẢI TỪNG FILE ĐÃ CHỌN VÀ LƯU VÀO THIẾT BỊ
    # =========================================================================

    # [30] REPEAT for each (selected)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.repeat.each",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_each,
            "WFControlFlowMode": 0,
            "WFInput": var_ref("selected")
        }
    })

    # [31] Set label_now = Repeat Item
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "label_now",
            "WFInput": {"Value": {"VariableName": "Repeat Item", "Type": "Variable"}, "WFSerializationType": "WFTextTokenAttachment"}
        }
    })

    # [32] Lấy link tải: media_url = medias[label_now]
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.getvalueforkey",
        "WFWorkflowActionParameters": {
            "UUID": u_media_url_act,
            "CustomOutputName": "media_url",
            "WFDictionaryKey": tok("\ufffc", {"{0, 1}": {"VariableName": "label_now", "Type": "Variable"}}),
            "WFInput": var_ref("medias")
        }
    })

    # [33] Tải file media về máy: downloadurl(media_url)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.downloadurl",
        "WFWorkflowActionParameters": {
            "UUID": u_media_file,
            "CustomOutputName": "media_file",
            "ShowHeaders": False,
            "WFHTTPMethod": "GET",
            "WFURL": tok("\ufffc", {
                "{0, 1}": {
                    "OutputUUID": u_media_url_act,
                    "OutputName": "media_url",
                    "Type": "ActionOutput",
                    "Aggrandizements": [agg_url()]
                }
            }),
            "WFHTTPHeaders": {
                "Value": {
                    "WFDictionaryFieldValueItems": [{
                        "WFKey": tok("User-Agent"),
                        "WFItemType": 0,
                        "WFValue": tok(UA())
                    }]
                },
                "WFSerializationType": "WFDictionaryFieldValue"
            }
        }
    })

    # [34] IF label_now chứa ký hiệu "🎵" (Âm thanh MP3) → Lưu vào Tệp (Files)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_is_audio,
            "WFControlFlowMode": 0,
            "WFCondition": 99,   # Contains
            "WFConditionalActionString": "🎵",
            "WFInput": {"Type": "Variable", "Variable": var_ref("label_now", [agg_str()])}
        }
    })
    # [35] Lưu file âm thanh vào Files (cho phép chọn nơi lưu hoặc iCloud)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.documentpicker.save",
        "WFWorkflowActionParameters": {
            "WFFileStorageService": "iCloud Drive",
            "SelectionMode": "Save",
            "WFInput": act_out(u_media_file, "media_file")
        }
    })

    # [36] ELSE → Video hoặc Ảnh → Lưu trực tiếp vào Album Ảnh (Photos)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_is_audio, "WFControlFlowMode": 1}
    })
    # [37] Lưu vào Photos (Cuộn camera)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.savetocameraroll",
        "WFWorkflowActionParameters": {
            "WFInput": act_out(u_media_file, "media_file")
        }
    })

    # [38] END IF is_audio
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_is_audio, "WFControlFlowMode": 2}
    })

    # [39] END REPEAT
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.repeat.each",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_each, "WFControlFlowMode": 2}
    })

    # =========================================================================
    # PHASE 5: THÔNG BÁO HOÀN TẤT
    # =========================================================================

    # [40] Thông báo hoàn tất
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.showresult",
        "WFWorkflowActionParameters": {
            "Text": tok("✅ Đã tải xong!\n\nKiểm tra ảnh/video trong Photos (🎬🖼️) hoặc Tệp (🎵 âm thanh).")
        }
    })

    # ──────────────────────────────────────────────────────────────────────────
    all_content_classes = [
        "WFAppStoreAppContentItem", "WFArticleContentItem", "WFContactContentItem",
        "WFDateContentItem", "WFEmailAddressContentItem", "WFGenericFileContentItem",
        "WFImageContentItem", "WFiTunesProductContentItem", "WFLocationContentItem",
        "WFDCMapsLinkContentItem", "WFAVAssetContentItem", "WFPDFContentItem",
        "WFPhoneNumberContentItem", "WFRichTextContentItem", "WFSafariWebPageContentItem",
        "WFStringContentItem", "WFURLContentItem"
    ]

    print(f"  Total actions built: {len(A)} actions")

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


def audit_workflow(wf):
    """
    Rà soát toàn diện cấu trúc AST của Shortcut:
    - Block control flow modes (0, 1, 2) và nesting stack
    - Menu structure: items list, case branches, proper termination
    - Conditionals: condition codes, required comparison strings
    - OpenURL: WFURL presence
    - Variable references: initialization before use
    - OutputUUID references: definition before use
    """
    actions = wf.get("WFWorkflowActions", [])
    errors = []
    block_stack = []
    defined_vars = set()
    defined_uuids = set()

    for idx, act in enumerate(actions):
        ident = act.get("WFWorkflowActionIdentifier", "")
        params = act.get("WFWorkflowActionParameters", {})
        grp = params.get("GroupingIdentifier")
        mode = params.get("WFControlFlowMode")
        uuid_val = params.get("UUID")

        if uuid_val:
            defined_uuids.add(uuid_val)

        # Track setvariable
        if ident == "is.workflow.actions.setvariable":
            vname = params.get("WFVariableName")
            if vname:
                defined_vars.add(vname)

        # 1. Block structure check
        if grp:
            if mode == 0:
                block_stack.append((grp, ident, idx, params))
            elif mode == 1:
                if not block_stack:
                    errors.append(f"[{idx}] {ident} mode 1 with no open block (grp={grp})")
                elif block_stack[-1][0] != grp:
                    errors.append(f"[{idx}] {ident} mode 1 grp mismatch: expected {block_stack[-1][0]}, got {grp}")
            elif mode == 2:
                if not block_stack:
                    errors.append(f"[{idx}] {ident} mode 2 with no open block (grp={grp})")
                else:
                    open_grp, open_ident, open_idx, _ = block_stack.pop()
                    if open_grp != grp:
                        errors.append(f"[{idx}] {ident} mode 2 mismatched block: opened by [{open_idx}] {open_ident} ({open_grp}) but closed with {grp}")
            else:
                errors.append(f"[{idx}] {ident} unknown WFControlFlowMode: {mode}")

        # 2. choosefrommenu audit
        if ident == "is.workflow.actions.choosefrommenu":
            if mode == 0:
                items = params.get("WFMenuItems")
                if not isinstance(items, list) or not all(isinstance(x, str) for x in items):
                    errors.append(f"[{idx}] choosefrommenu mode 0: WFMenuItems must be list of strings, got {type(items)}")
            elif mode == 1:
                title = params.get("WFMenuItemTitle")
                if not title:
                    errors.append(f"[{idx}] choosefrommenu mode 1 missing WFMenuItemTitle")
            elif mode == 2:
                pass

        # 3. conditional audit
        if ident == "is.workflow.actions.conditional":
            if mode == 0:
                cond = params.get("WFCondition")
                if cond is None:
                    errors.append(f"[{idx}] conditional mode 0 missing WFCondition")
                elif cond in (4, 5, 99):  # Is, IsNot, Contains
                    match_str = params.get("WFConditionalActionString")
                    if not match_str:
                        errors.append(f"[{idx}] conditional mode 0 with cond={cond} missing non-empty WFConditionalActionString")

        # 4. openurl audit
        if ident == "is.workflow.actions.openurl":
            if "WFURL" not in params:
                errors.append(f"[{idx}] openurl missing WFURL parameter")

        # 5. downloadurl audit
        if ident == "is.workflow.actions.downloadurl":
            if "WFURL" not in params:
                errors.append(f"[{idx}] downloadurl missing WFURL parameter")

    if block_stack:
        for grp, ident, idx, _ in block_stack:
            errors.append(f"Unclosed block: [{idx}] {ident} (grp={grp})")

    if errors:
        print(f"❌ AUDIT FAILED with {len(errors)} error(s):")
        for err in errors:
            print(f"   • {err}")
        return False
    else:
        print("✅ AUDIT PASSED: 100% clean AST, no malformed control flow or parameters!")
        return True


def generate(source, signed, name):
    wf = build_workflow(shortcut_name=name)

    # Chạy audit trước khi tạo file
    if not audit_workflow(wf):
        print(f"❌ Không thể tạo shortcut '{name}' do lỗi audit!")
        sys.exit(1)

    with open(source, "wb") as f:
        plistlib.dump(wf, f)
    print(f"📦 Source: {source} ({len(wf['WFWorkflowActions'])} actions)")
    try:
        subprocess.run(
            ["shortcuts", "sign", "--mode", "anyone", "--input", source, "--output", signed],
            check=True
        )
        print(f"✅ Signed: {signed} ({os.path.getsize(signed):,} bytes)")
    except Exception as e:
        print(f"⚠️  Sign failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    generate("SnapAll_Source.shortcut", "SnapAll.shortcut", "SnapAll")
    generate("SnapVideo_Source.shortcut", "SnapVideo.shortcut", "Snap Video")
