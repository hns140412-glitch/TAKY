#!/usr/bin/env node
import fs from "node:fs";

const path = "PROJECTS/LEARNING_APP_FAMILY_CHARACTER_FORMATION_CONTRACT_2026-09-23.json";
const data = JSON.parse(fs.readFileSync(path, "utf8"));

const fail = (msg) => {
  console.error("FAIL:", msg);
  process.exitCode = 1;
};

const expectedCore6 = ["Dooby","Rory","Ink","Nova","Take","Zero"];
const expectedRuntimeLock = ["USER_PHOTO","SIGNATURE_ITEM","DIRECTION_1","DIRECTION_2"];
const expectedItems = ["CAMERA","COMPASS","EXPLORATION_NOTEBOOK","BINOCULARS","WATER_BOTTLE"];

if (JSON.stringify(data.core6?.order) !== JSON.stringify(expectedCore6)) fail("Core 6 order drift");
if (data.core6?.canonical_bind !== "EXISTS") fail("CANONICAL_BIND must remain EXISTS");
if (data.core6?.visual_id_state !== "HARD_LOCK") fail("Core 6 Visual ID must remain HARD_LOCK");
if (data.authority?.reopen_core6_visual_id !== false) fail("Core 6 Visual ID must not reopen");
if (data.world?.setup_space !== "PRE_TRAVEL_PACKING_PREPARATION_SPACE") fail("Character Formation world drift");
if (data.world?.island_role !== "DESTINATION_HINT_ONLY") fail("Island must remain destination hint only");
if (JSON.stringify(data.existing_runtime_sequence_lock) !== JSON.stringify(expectedRuntimeLock)) fail("Photo -> Signature Item -> Direction 1 -> Direction 2 order regression");
if (JSON.stringify(data.signature_item_enum) !== JSON.stringify(expectedItems)) fail("Signature Item enum drift");
if (data.rendering_contract?.whole_mockup_crop_as_runtime !== false) fail("Whole mockup crop runtime is forbidden");
if (data.motion?.default_tier !== "CHARACTER_ONLY_SENSOR_DEPTH") fail("Sensor depth tier drift");
if (data.motion?.ui_sensor_motion !== false) fail("UI must not move with sensor depth");
if (data.motion?.reduced_motion_fallback !== "STATIC_DEPTH") fail("Reduced-motion fallback missing");
if (data.validation?.viewport !== "390x844") fail("390x844 validation viewport required");
if (data.validation?.anchor_regression_required !== true) fail("Anchor regression check required");
if (data.validation?.reject_before_user_exposure_on_mismatch !== true) fail("NO PASS -> NO SHOW required");

if (!process.exitCode) console.log("PASS: Learning App Family Character Formation contract hard locks intact");
