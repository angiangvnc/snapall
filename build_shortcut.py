#!/usr/bin/env python3
"""
SnapAll v11.0 – Viết lại hoàn toàn từ đầu.
Flow rõ ràng:
  1. Get URL (Share Sheet hoặc menu "Enter video link")
  2. Gọi API → JSON {labels, medias, menu_title, ...}
  3. choosefromlist HD/MP3/... → user chọn
  4. Download từng file đã chọn → lưu vào Photos/Files
  5. Thông báo hoàn tất
"""

import plistlib
import os
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
    g_api_err   = uid()
    g_no_sel    = uid()
    g_each      = uid()
    g_is_audio  = uid()
    g_is_image  = uid()

    MENU_ENTER = "💬 Enter video link"
    MENU_GUIDE = "📖 User guide"
    MENU_SHARE = "⚠️ Not showing in the share sheet?"
    MENU_HIDE  = "⚙️ Hide this menu next time"

    # =========================================================================
    # PHASE 1: LẤY URL (Share Sheet hoặc nhập tay)
    # =========================================================================

    # [0] IF ExtensionInput has NO value (chạy trực tiếp, không qua Share Sheet)
    # Check ExtensionInput TRỰC TIẾP - không qua biến trung gian để tránh mất giá trị
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

    # [2] choosefrommenu "Choose an action" (giống Snap Video)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefrommenu",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_menu,
            "WFControlFlowMode": 0,
            "WFMenuPrompt": tok("Choose an action"),
            "WFMenuItems": [MENU_ENTER, MENU_GUIDE, MENU_SHARE, MENU_HIDE]
        }
    })

    # [3] CASE: Enter video link
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefrommenu",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_menu, "WFControlFlowMode": 0, "WFMenuItemTitle": MENU_ENTER
        }
    })
    # [4] Ask for URL
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.ask",
        "WFWorkflowActionParameters": {
            "UUID": u_ask_url,
            "WFAskActionPrompt": tok("💬 Nhập link video (TikTok, Facebook, ...):"),
            "WFAskActionDefaultAnswer": tok(""),
            "WFAskActionKeyboardType": "URL"
        }
    })
    # [5] Set shared_url = entered URL
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "shared_url",
            "WFInput": act_out(u_ask_url, "Provided Input")
        }
    })

    # [6] CASE: User guide
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefrommenu",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_menu, "WFControlFlowMode": 0, "WFMenuItemTitle": MENU_GUIDE
        }
    })
    # [7] Open guide
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.openurl",
        "WFWorkflowActionParameters": {"WFURL": tok("https://snapall.vercel.app/")}
    })
    # [8] Exit
    A.append({"WFWorkflowActionIdentifier": "is.workflow.actions.exit", "WFWorkflowActionParameters": {}})

    # [9] CASE: Not showing in share sheet?
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefrommenu",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_menu, "WFControlFlowMode": 0, "WFMenuItemTitle": MENU_SHARE
        }
    })
    # [10] Open Apple help
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.openurl",
        "WFWorkflowActionParameters": {"WFURL": tok("https://support.apple.com/guide/shortcuts/use-shortcuts-in-apps-apd886daaaf3/ios")}
    })
    # [11] Exit
    A.append({"WFWorkflowActionIdentifier": "is.workflow.actions.exit", "WFWorkflowActionParameters": {}})

    # [12] CASE: Hide this menu next time
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefrommenu",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_menu, "WFControlFlowMode": 0, "WFMenuItemTitle": MENU_HIDE
        }
    })
    # [13] Exit
    A.append({"WFWorkflowActionIdentifier": "is.workflow.actions.exit", "WFWorkflowActionParameters": {}})

    # [14] END choosefrommenu
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefrommenu",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_menu, "WFControlFlowMode": 2}
    })

    # [14b] ELSE: có ExtensionInput từ Share Sheet → set shared_url
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_no_input, "WFControlFlowMode": 1}
    })
    # [14c] Set shared_url = ExtensionInput (coerce to String)
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

    # [15] END IF no_input
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_no_input, "WFControlFlowMode": 2}
    })

    # =========================================================================
    # PHASE 2: GỌI API → JSON
    # =========================================================================

    # [16] base64encode(shared_url) → b64
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.base64encode",
        "WFWorkflowActionParameters": {
            "UUID": u_b64,
            "WFBase64LineBreakMode": "None",
            "WFInput": var_ref("shared_url", [agg_str()])
        }
    })

    # [17] URL: API_URL?b64={b64} → api_url
    api_str = f"{API_URL}?b64=\ufffc"
    o_b64 = len(f"{API_URL}?b64=")
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.url",
        "WFWorkflowActionParameters": {
            "UUID": u_api_url,
            "WFURLActionURL": tok(api_str, {
                f"{{{o_b64}, 1}}": {
                    "OutputUUID": u_b64,
                    "OutputName": "Đã mã hóa Base64",
                    "Type": "ActionOutput"
                }
            })
        }
    })

    # [18] downloadurl(api_url) → api_json  (Content-Type: application/json → auto dict)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.downloadurl",
        "WFWorkflowActionParameters": {
            "UUID": u_api_json,
            "CustomOutputName": "api_json",
            "ShowHeaders": False,
            "WFHTTPMethod": "GET",
            "WFURL": tok("\ufffc", {
                "{0, 1}": {
                    "OutputUUID": u_api_url,
                    "OutputName": "URL",
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

    # =========================================================================
    # PHASE 3: KIỂM TRA LỖI + HIỆN MENU CHỌN ĐỊNH DẠNG
    # =========================================================================

    # [19] IF api_json["status"] == "error" → báo lỗi + exit
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
    # [20] Show error message
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
    # [21] Exit
    A.append({"WFWorkflowActionIdentifier": "is.workflow.actions.exit", "WFWorkflowActionParameters": {}})

    # [22] END IF api_err
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_api_err, "WFControlFlowMode": 2}
    })

    # [23] Set medias = api_json["medias"]  (dùng sau trong vòng lặp)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "medias",
            "WFInput": var_ref("api_json", agg_dict_key("medias"))
        }
    })

    # [24] choosefromlist → selected (menu HD/MP3/...)
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
            "WFChooseFromListActionSelectAll": True,
            "WFInput": var_ref("api_json", agg_dict_key("labels"))
        }
    })

    # [25] IF selected has NO value → exit (người dùng bấm Cancel)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_no_sel,
            "WFControlFlowMode": 0,
            "WFCondition": 101,   # Does not have a value
            "WFInput": {"Type": "Variable", "Variable": act_out(u_selected, "selected")}
        }
    })
    # [26] Exit
    A.append({"WFWorkflowActionIdentifier": "is.workflow.actions.exit", "WFWorkflowActionParameters": {}})
    # [27] END IF no_sel
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_no_sel, "WFControlFlowMode": 2}
    })

    # =========================================================================
    # PHASE 4: DOWNLOAD TỪNG FILE ĐƯỢC CHỌN
    # =========================================================================

    # [28] REPEAT for each (selected)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.repeat.each",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": g_each,
            "WFControlFlowMode": 0,
            "WFInput": act_out(u_selected, "selected")
        }
    })

    # [29] Set label_now = Repeat Item (label đã chọn)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "label_now",
            "WFInput": {"Value": {"VariableName": "Repeat Item", "Type": "Variable"}, "WFSerializationType": "WFTextTokenAttachment"}
        }
    })

    # [30] Get media_url = medias[label_now]
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.getvalueforkey",
        "WFWorkflowActionParameters": {
            "UUID": u_media_url_act,
            "CustomOutputName": "media_url",
            "WFDictionaryKey": tok("\ufffc", {"{0, 1}": {"VariableName": "label_now", "Type": "Variable"}}),
            "WFInput": var_ref("medias")
        }
    })

    # [31] downloadurl(media_url) → media_file
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

    # [32] IF label_now contains "🎵" → lưu vào Files (audio)
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
    # [33] Save audio to Files (iCloud Drive / On My iPhone)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.documentpicker.save",
        "WFWorkflowActionParameters": {
            "WFFileStorageService": "iCloud Drive",
            "SelectionMode": "Save",
            "WFInput": act_out(u_media_file, "media_file")
        }
    })

    # [34] ELSE → lưu vào Photos (video + ảnh)
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_is_audio, "WFControlFlowMode": 1}
    })
    # [35] Save photo/video to Camera Roll
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.savetocameraroll",
        "WFWorkflowActionParameters": {
            "WFCameraRollSelectedGroup": "Saved Photos",
            "WFInput": act_out(u_media_file, "media_file")
        }
    })

    # [36] END IF is_audio
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_is_audio, "WFControlFlowMode": 2}
    })

    # [37] END REPEAT for each
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.repeat.each",
        "WFWorkflowActionParameters": {"GroupingIdentifier": g_each, "WFControlFlowMode": 2}
    })

    # =========================================================================
    # PHASE 5: HOÀN TẤT
    # =========================================================================

    # [38] Show result: "✅ Đã tải xong! Kiểm tra Photos/Files."
    A.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.showresult",
        "WFWorkflowActionParameters": {
            "Text": tok("✅ Đã tải xong!\n\nKiểm tra ảnh/video trong Photos (🎬🖼️) hoặc Files (🎵 âm thanh).")
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

    print(f"  Total actions built: {len(A)} actions (clean rewrite v11.0)")

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
