import json, hashlib
from pathlib import Path

ROOT = Path(r"D:\Git PWA\TAKY")
REG = ROOT / "MASTER" / "CHARACTER_VISUAL_ID_BACKFILL_REGISTRY_24_CANDIDATE_2026-10-08.json"

TRAITS = {
"13": {
  "character_class":"ANIMAL","species_or_body_type":"CAPYBARA_BIPED",
  "head_face":{
    "shape":"broad rounded capybara head with long soft muzzle",
    "eyes":{"shape":"large rounded-almond","size":"large","spacing":"medium-wide","angle":"calm","iris_color":"deep brown","distinctive":"dark rim with warm glossy highlights"},
    "brows":{"shape":"soft straight arch","weight":"medium"},
    "nose_muzzle_beak":{"structure":"large broad dark-brown capybara nose at end of elongated muzzle","distinctive":"wide rounded muzzle dominates face silhouette"},
    "mouth_lips":{"shape":"small relaxed closed smile","distinctive":"subtle curved mouth below broad muzzle"},
    "ears_horns_antennae":{"structure":"small rounded ears set laterally"},
    "hair_fur_feather":{"silhouette":"short even warm-tan fur","texture":"short dense plush fur","hairline_or_pattern":"uniform tan head with slightly darker muzzle/nose region"},
    "base_tone":"warm tan / caramel",
    "unique_marks":["broad capybara muzzle","small round ears","teal flower ear accessory"],
    "resting_expression":"calm friendly smile"
  },
  "costume":{"identity_critical":["blue-white cap","turquoise hoodie","cream-blue explorer jacket","dark shorts","blue-white sneakers","navy backpack"],"signature_accessories":["teal flower ear accessory","gold star hardware"],"signature_equipment":["backpack with rolled mat"],"materials":["short plush fur","woven cap/hoodie/jacket","shorts textile","leather-like straps","metallic gold hardware","rubber sneaker sole"]},
  "palette":["warm tan","caramel brown","turquoise","royal blue","off-white","charcoal","gold"]
},
"14": {
  "character_class":"ANIMAL","species_or_body_type":"MONKEY_BIPED",
  "head_face":{
    "shape":"round monkey face with pale peach facial field",
    "eyes":{"shape":"very large rounded","size":"large","spacing":"wide","angle":"soft","iris_color":"amber-brown","distinctive":"large glossy highlights and dark upper lash line"},
    "brows":{"shape":"soft medium arch","weight":"medium"},
    "nose_muzzle_beak":{"structure":"small subtle monkey nose centered on pale face","distinctive":"low-profile nose"},
    "mouth_lips":{"shape":"wide open cheerful smile","distinctive":"small visible upper teeth/fangs in source pose"},
    "ears_horns_antennae":{"structure":"very large round protruding ears with pink inner ear"},
    "hair_fur_feather":{"silhouette":"layered medium-brown crown hair/fur with soft side tufts","texture":"soft dense fur/hair","hairline_or_pattern":"brown crown around pale peach facial field"},
    "base_tone":"medium brown + pale peach",
    "unique_marks":["very large round ears","long curled prehensile tail"],
    "resting_expression":"energetic cheerful smile"
  },
  "costume":{"identity_critical":["blue-white cap","yellow hoodie","cream-blue explorer jacket","dark shorts","blue-yellow sneakers","navy backpack"],"signature_accessories":["gold star hardware","dark fingerless handlike paw glove"],"signature_equipment":["backpack"],"materials":["soft fur","woven cap/hoodie/jacket","shorts textile","leather-like straps","metallic gold hardware","rubber sneaker sole"]},
  "palette":["medium brown","pale peach","sunny yellow","royal blue","off-white","charcoal","gold"]
},
"15": {
  "character_class":"ANIMAL","species_or_body_type":"CHAMELEON_BIPED",
  "head_face":{
    "shape":"rounded reptilian head with broad cheek line and tapered snout",
    "eyes":{"shape":"large rounded chameleon eye","size":"large","spacing":"wide","angle":"independently expressive","iris_color":"deep brown/green in visible eye","distinctive":"eye-direction fidelity is identity-critical"},
    "brows":{"shape":"minimal raised brow ridge","weight":"minimal"},
    "nose_muzzle_beak":{"structure":"small nostril openings on short reptilian snout","distinctive":"no mammalian nose"},
    "mouth_lips":{"shape":"broad reptilian smile","distinctive":"wide curved mouth with small teeth visible in source pose"},
    "ears_horns_antennae":{"structure":"no external ears; smooth reptilian side-head silhouette"},
    "hair_fur_feather":{"silhouette":"smooth scaleless/plush-rendered reptilian crown with small crest-like top contour","texture":"smooth matte skin","hairline_or_pattern":"green base with yellow/orange/coral mottled patches"},
    "base_tone":"bright green with yellow/orange/coral mottling",
    "unique_marks":["multicolor mottled skin","tight spiral curled tail"],
    "resting_expression":"playful broad smile"
  },
  "costume":{"identity_critical":["blue-white cap worn slightly angled/back","teal hoodie","cream-blue explorer jacket","dark shorts","green/teal sneakers","navy backpack"],"signature_accessories":["gold star hardware","fingerless claw-hand wraps"],"signature_equipment":["backpack with rolled mat"],"materials":["smooth reptilian skin","woven cap/hoodie/jacket","shorts textile","leather-like straps","metallic gold hardware","rubber sneaker sole"]},
  "palette":["bright green","lime","yellow","orange/coral spots","teal","royal blue","off-white","gold"]
},
"16": {
  "character_class":"ANIMAL","species_or_body_type":"DUCK_BIPED",
  "head_face":{
    "shape":"round duck head with fluffy white feather cheeks",
    "eyes":{"shape":"very large rounded","size":"large","spacing":"wide","angle":"soft","iris_color":"bright blue","distinctive":"dark upper lashes with strong glossy highlights"},
    "brows":{"shape":"small pale feather-brow marks","weight":"light"},
    "nose_muzzle_beak":{"structure":"broad orange-yellow duck beak","distinctive":"wide rounded beak with pronounced upper bill"},
    "mouth_lips":{"shape":"wide open cheerful beak-mouth","distinctive":"pink mouth interior visible"},
    "ears_horns_antennae":{"structure":"no external ears; feather silhouette only"},
    "hair_fur_feather":{"silhouette":"soft white feather crown/cheeks with layered wing feathers","texture":"soft layered white feathers","hairline_or_pattern":"all-white plumage with slight cream warmth"},
    "base_tone":"white/cream plumage + orange-yellow beak/legs",
    "unique_marks":["large layered white wings","blue flower/daisy cap accessory","orange legs"],
    "resting_expression":"bright joyful smile"
  },
  "costume":{"identity_critical":["blue-white cap","blue hoodie","cream-blue explorer jacket","dark shorts","blue-white sneakers","navy backpack"],"signature_accessories":["blue-white daisy cap ornament","gold star hardware"],"signature_equipment":["backpack with rolled mat"],"materials":["layered feathers","woven cap/hoodie/jacket","shorts textile","leather-like straps","metallic gold hardware","rubber sneaker sole"]},
  "palette":["white","cream","bright blue","navy","orange-yellow","charcoal","gold"]
},
"17": {
  "character_class":"ANIMAL","species_or_body_type":"MOLE_BIPED",
  "head_face":{
    "shape":"round compact mole-like head with broad pale muzzle and cheek field",
    "eyes":{"shape":"large rounded","size":"large","spacing":"wide","angle":"soft","iris_color":"warm brown/amber","distinctive":"glossy highlights under cap brim"},
    "brows":{"shape":"short soft dark arch","weight":"medium"},
    "nose_muzzle_beak":{"structure":"small pink rounded nose centered on pale muzzle","distinctive":"prominent whiskers extend laterally"},
    "mouth_lips":{"shape":"wide open cheerful smile","distinctive":"small visible upper teeth in source pose"},
    "ears_horns_antennae":{"structure":"small low round ears largely blending into fur silhouette"},
    "hair_fur_feather":{"silhouette":"short smooth medium-brown fur","texture":"soft dense plush fur","hairline_or_pattern":"brown crown with pale cream muzzle/cheek field"},
    "base_tone":"medium brown + pale cream",
    "unique_marks":["long white whiskers","pink nose","compact short-tail body"],
    "resting_expression":"cheerful open smile"
  },
  "costume":{"identity_critical":["blue-white cap","grey hoodie","cream-blue explorer jacket","dark shorts","blue-white sneakers","navy backpack"],"signature_accessories":["gold star hardware"],"signature_equipment":["backpack with rolled mat"],"materials":["short plush fur","woven cap/hoodie/jacket","shorts textile","leather-like straps","metallic gold hardware","rubber sneaker sole"]},
  "palette":["medium brown","pale cream","grey","royal blue","off-white","charcoal","gold"]
},
"18": {
  "character_class":"ANIMAL","species_or_body_type":"KOALA_BIPED",
  "head_face":{
    "shape":"round koala head with oversized fluffy ears and short muzzle",
    "eyes":{"shape":"very large rounded","size":"large","spacing":"wide","angle":"soft","iris_color":"violet-purple","distinctive":"dark lashes and bright glossy highlights; one-eye wink in source pose"},
    "brows":{"shape":"soft pale-grey arch","weight":"light"},
    "nose_muzzle_beak":{"structure":"very large oval dark koala nose","distinctive":"nose is dominant central facial anchor"},
    "mouth_lips":{"shape":"small open cheerful smile","distinctive":"pink tongue visible in source pose"},
    "ears_horns_antennae":{"structure":"very large round fluffy ears with broad pink inner ear"},
    "hair_fur_feather":{"silhouette":"soft pale grey-white fur with short crown tuft","texture":"longer fluffy plush fur around ears/cheeks","hairline_or_pattern":"uniform pale coat with slightly darker nose/eye accents"},
    "base_tone":"pale grey-white",
    "unique_marks":["oversized fluffy ears","large dark oval nose","violet eye"],
    "resting_expression":"playful cheerful smile"
  },
  "costume":{"identity_critical":["blue-white cap","purple hoodie","cream explorer jacket","dark shorts","purple-white sneakers","navy backpack"],"signature_accessories":["gold star hardware"],"signature_equipment":["camera","backpack with rolled mat"],"materials":["fluffy fur","woven cap/hoodie/jacket","shorts textile","camera metal/plastic","leather-like straps","metallic gold hardware","rubber sneaker sole"]},
  "palette":["pale grey-white","purple","violet","royal blue","off-white","charcoal","gold"]
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
print("PASS: Visual ID detail backfill 13-18 = 6/6")
