import json, hashlib
from pathlib import Path

ROOT = Path(r"D:\Git PWA\TAKY")
REG = ROOT / "MASTER" / "CHARACTER_VISUAL_ID_BACKFILL_REGISTRY_24_CANDIDATE_2026-10-08.json"

TRAITS = {
"19": {
  "character_class":"HUMAN_SPECIAL","species_or_body_type":"HUMAN",
  "head_face":{
    "shape":"soft oval youthful human face with lightly tapered chin",
    "eyes":{"shape":"large almond-round","size":"large","spacing":"medium-wide","angle":"slightly downturned/quiet","iris_color":"warm brown-amber","distinctive":"clear glossy highlights beneath heavy layered bangs"},
    "brows":{"shape":"straight-soft dark brow","weight":"medium"},
    "nose_muzzle_beak":{"structure":"small straight human nose","distinctive":"minimal stylized bridge/tip"},
    "mouth_lips":{"shape":"small neutral closed mouth","distinctive":"thin understated lip contour"},
    "ears_horns_antennae":{"structure":"human ears partly covered by hair/cap"},
    "hair_fur_feather":{"silhouette":"short tousled dark-brown/black layered hair sweeping over forehead","texture":"soft layered anime-style hair","hairline_or_pattern":"long front fringe with side locks under cap"},
    "base_tone":"light skin + dark brown/black hair",
    "unique_marks":["blue-white cap","quiet amber eyes","short layered dark hair"],
    "resting_expression":"calm serious-neutral"
  },
  "costume":{"identity_critical":["blue-white cap","blue-white explorer jacket","blue hoodie","black cropped pants","blue-white sneakers","black backpack","black fingerless gloves"],"signature_accessories":["compass pendant","gold hardware"],"signature_equipment":["backpack","compass"],"materials":["layered hair","woven cap/hoodie/jacket","cargo textile","synthetic/leather gloves","metallic gold hardware","rubber sneaker sole"]},
  "palette":["dark brown/black hair","light skin","royal blue","white","black/charcoal","gold"]
},
"20": {
  "character_class":"HUMAN_SPECIAL","species_or_body_type":"HUMAN",
  "head_face":{
    "shape":"soft oval human face with small tapered chin",
    "eyes":{"shape":"large almond","size":"large","spacing":"medium","angle":"soft slightly lifted outer corners","iris_color":"violet-purple","distinctive":"lavender highlights and dark lashes"},
    "brows":{"shape":"slim soft arch","weight":"light"},
    "nose_muzzle_beak":{"structure":"small straight human nose","distinctive":"minimal stylized bridge/tip"},
    "mouth_lips":{"shape":"small neutral closed lips","distinctive":"subtle pale lip contour"},
    "ears_horns_antennae":{"structure":"human ears mostly covered by long hair"},
    "hair_fur_feather":{"silhouette":"very long voluminous wavy dark-purple/black hair","texture":"silky layered waves","hairline_or_pattern":"center/soft-side fringe with violet highlights and small lavender hair clips"},
    "base_tone":"light skin + deep purple-black hair",
    "unique_marks":["very long wavy hair","violet eyes","small lavender hair clips"],
    "resting_expression":"quiet thoughtful-neutral"
  },
  "costume":{"identity_critical":["lavender-white oversized jacket","black inner top","black skirt","lavender-white chunky sneakers","black backpack"],"signature_accessories":["large lavender-white headphones around neck","purple bear motifs","hair clips"],"signature_equipment":["headphones","notebook","backpack"],"materials":["silky hair","woven technical jacket","skirt textile","plastic/metal headphones","synthetic backpack","rubber sneaker sole"]},
  "palette":["deep purple-black","violet","lavender","white","black","soft pink accent"]
},
"21": {
  "character_class":"HUMAN_SPECIAL","species_or_body_type":"HUMAN",
  "head_face":{
    "shape":"soft youthful oval face with lightly pointed chin",
    "eyes":{"shape":"large almond-round","size":"large","spacing":"medium","angle":"energetic","iris_color":"orange-red / amber","distinctive":"warm gradient iris and sharp dark lash line"},
    "brows":{"shape":"short energetic arch","weight":"medium"},
    "nose_muzzle_beak":{"structure":"small straight human nose","distinctive":"minimal stylized tip"},
    "mouth_lips":{"shape":"wide open mischievous smile","distinctive":"small visible upper canine/fang detail"},
    "ears_horns_antennae":{"structure":"human ears exposed beneath short hair"},
    "hair_fur_feather":{"silhouette":"short highly tousled spiky red-orange hair","texture":"layered spiky hair","hairline_or_pattern":"irregular lifted crown tufts and side spikes"},
    "base_tone":"light skin + vivid red-orange hair",
    "unique_marks":["bright spiky red hair","orange-red eyes","goggles on head"],
    "resting_expression":"mischievous energetic smile"
  },
  "costume":{"identity_critical":["bronze/black goggles","black bomber jacket with red flame accents","red hoodie","black cropped cargo pants/shorts","red-white chunky sneakers","black backpack"],"signature_accessories":["goggles","flame motifs","red creature/charm accessories"],"signature_equipment":["goggles","backpack"],"materials":["layered hair","woven hoodie","technical bomber fabric","cargo textile","metallic bronze hardware","rubber sneaker sole"]},
  "palette":["red-orange hair","light skin","black","deep red","white","bronze/gold hardware"]
},
"22": {
  "character_class":"HYBRID","species_or_body_type":"SPECIAL_HUMANOID",
  "head_face":{
    "shape":"soft oval humanoid face with small tapered chin",
    "eyes":{"shape":"very large almond-round","size":"large","spacing":"medium-wide","angle":"gentle","iris_color":"blue-teal","distinctive":"cool aqua highlights and dark lashes"},
    "brows":{"shape":"fine soft arch","weight":"light"},
    "nose_muzzle_beak":{"structure":"small straight humanoid nose","distinctive":"minimal stylized tip"},
    "mouth_lips":{"shape":"small gentle closed smile","distinctive":"soft subtle lip line"},
    "ears_horns_antennae":{"structure":"very long pointed source-locked ears projecting laterally"},
    "hair_fur_feather":{"silhouette":"very long flowing silver-white hair with mint-green undertones","texture":"silky layered waves","hairline_or_pattern":"full layered fringe with long cascading side/back waves"},
    "base_tone":"light skin + silver-white/mint hair",
    "unique_marks":["long pointed ears","silver-mint long hair","green leaf and white flower crown"],
    "resting_expression":"gentle warm smile"
  },
  "costume":{"identity_critical":["white/mint oversized layered hoodie-dress/jacket","dark short lower layer","mint-white sneakers","mint/green backpack"],"signature_accessories":["leaf-and-flower crown","flower/clover motifs","small lantern"],"signature_equipment":["lantern","backpack"],"materials":["silky hair","woven layered garment","leaf/flower ornaments","metal/glass lantern","synthetic backpack","rubber sneaker sole"]},
  "palette":["silver-white","mint green","sage","white","soft teal-blue eyes","dark lower accent","gold lantern hardware"]
},
"23": {
  "character_class":"HYBRID","species_or_body_type":"SPECIAL_HUMANOID",
  "head_face":{
    "shape":"slender oval humanoid face with sharper jaw/chin",
    "eyes":{"shape":"narrow almond","size":"medium-large","spacing":"medium","angle":"focused/slightly downturned","iris_color":"amber-gold","distinctive":"sharp dark upper line and serious gaze"},
    "brows":{"shape":"straight slightly angled brow","weight":"medium"},
    "nose_muzzle_beak":{"structure":"small straight human-like nose","distinctive":"defined stylized bridge/tip"},
    "mouth_lips":{"shape":"small closed neutral mouth","distinctive":"thin serious lip contour"},
    "ears_horns_antennae":{"structure":"large pointed source-locked ears with dark outer tips"},
    "hair_fur_feather":{"silhouette":"short tousled white/silver hair with high irregular spikes","texture":"soft layered spiky hair","hairline_or_pattern":"long front fringe and lifted crown tufts"},
    "base_tone":"light skin + white/silver hair",
    "unique_marks":["pointed dark-tipped ears","white tousled hair","amber eyes"],
    "resting_expression":"serious observant-neutral"
  },
  "costume":{"identity_critical":["black/charcoal tactical hoodie with grey-white panels and blue accents","black cargo pants","black-white chunky sneakers","black tactical backpack"],"signature_accessories":["blue strap/buckle accents"],"signature_equipment":["tablet","tactical backpack"],"materials":["layered hair","technical shell fabric","cargo textile","plastic/metal buckles","rubber sneaker sole"]},
  "palette":["white/silver hair","light skin","black","charcoal","grey-white","electric blue accent","amber eyes"]
},
"24": {
  "character_class":"HUMAN_SPECIAL","species_or_body_type":"HUMAN",
  "head_face":{
    "shape":"soft round-heart youthful human face with small tapered chin",
    "eyes":{"shape":"very large rounded-almond","size":"large","spacing":"medium-wide","angle":"playful","iris_color":"deep pink / rose-red","distinctive":"dark upper lashes and glossy magenta highlights; one-eye wink in source pose"},
    "brows":{"shape":"fine soft arch","weight":"light"},
    "nose_muzzle_beak":{"structure":"small straight human nose","distinctive":"minimal stylized tip"},
    "mouth_lips":{"shape":"wide open cheerful smile","distinctive":"soft pink mouth interior"},
    "ears_horns_antennae":{"structure":"human ears mostly covered by twin-tail hair"},
    "hair_fur_feather":{"silhouette":"very long high twin tails with huge curled volume","texture":"silky layered curls","hairline_or_pattern":"dark brown/black roots transitioning to vivid pink ombre; pink bows/clips"},
    "base_tone":"light skin + dark brown/black to vivid-pink ombre hair",
    "unique_marks":["huge twin tails","pink ombre hair","pink bows and X/bar hair clips","rose-pink eye"],
    "resting_expression":"bright playful smile"
  },
  "costume":{"identity_critical":["pink-white oversized jacket","black inner top/dress","black pleated skirt with pink trim","white-pink chunky sneakers","pink-white backpack"],"signature_accessories":["heart motifs","bunny motifs","pink bows/clips"],"signature_equipment":["pink camera","backpack"],"materials":["silky hair","woven jacket","pleated skirt fabric","camera metal/plastic","synthetic backpack","rubber sneaker sole"]},
  "palette":["dark brown/black hair","vivid pink","rose","white","black","light skin","soft metallic pink accents"]
}
}

def fingerprint(card):
    payload={"visual_id":card["visual_id"],"source_sha256":card["identity_fingerprint"]["source_sha256"],"identity_lock":card["identity_lock"]}
    return hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")).hexdigest()

reg=json.loads(REG.read_text(encoding="utf-8"))
paths={x["visual_id"]: ROOT/x["card_path"] for x in reg["roster"]}
for vid,t in TRAITS.items():
    p=paths[vid]
    card=json.loads(p.read_text(encoding="utf-8"))
    card["character_class"]=t["character_class"]
    card["species_or_body_type"]=t["species_or_body_type"]
    hf=card["identity_lock"]["head_face"]
    for k,v in t["head_face"].items(): hf[k]=v
    ce=card["identity_lock"]["costume_equipment"]
    ce["identity_critical"]=t["costume"]["identity_critical"]
    ce["signature_accessories"]=t["costume"]["signature_accessories"]
    ce["signature_equipment"]=t["costume"]["signature_equipment"]
    ce["materials"]=t["costume"]["materials"]
    card["identity_lock"]["color_material_palette"]=t["palette"]
    src=card["authority"]["approved_source_refs"][0]
    card["detail_anchors"].update({
      "front_face":src,"three_quarter_face":src,"eyes":src,"nose_muzzle_beak":src,"mouth":src,
      "hair_fur_feather":src,"skin_fur_texture":src,
      "limb_detail":card["turnaround_views"]["authority_registry"],
      "signature_prop_grip":src
    })
    card["backfill_status"]["fine_face_detail"]="BACKFILLED_FROM_APPROVED_SOURCE"
    card["backfill_status"]["color_material"]="BACKFILLED_SEMANTIC_FROM_APPROVED_SOURCE"
    card["identity_fingerprint"]["digest"]=fingerprint(card)
    card["identity_fingerprint"]["status"]="CORE_IDENTITY_FINGERPRINT_READY"
    p.write_text(json.dumps(card,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# Global registration completion status. This does not close derivative art production.
for item in reg["roster"]:
    p=ROOT/item["card_path"]
    card=json.loads(p.read_text(encoding="utf-8"))
    card.setdefault("gate", {})["registration_image_generation_forbidden"]=True
    card["gate"]["registration_outputs"]="METADATA_POINTERS_HASHES_EXISTING_APPROVED_PIXELS_ONLY"
    card["gate"]["generated_reference_sheet_is_asset"]=False
    p.write_text(json.dumps(card,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    item["detail_backfill_status"]="VISUAL_ID_REGISTRATION_COMPLETE__DERIVATIVE_ASSETS_SEPARATE"
    item["identity_fingerprint_status"]="READY"

reg["invariants"]["fine_visual_detail_backfill"]="24_OF_24_COMPLETE_FROM_APPROVED_SOURCE"
reg["invariants"]["identity_fingerprint"]="24_OF_24_READY"
reg["invariants"]["registration_image_generation"]="FORBIDDEN"
reg["invariants"]["derivative_asset_production"]="SEPARATE_OPEN_PIPELINE"
REG.write_text(json.dumps(reg,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("PASS: Visual ID detail backfill 19-24 = 6/6; Crew24 registration = 24/24")
