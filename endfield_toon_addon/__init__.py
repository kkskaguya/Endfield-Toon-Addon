bl_info = {
    "name": "Endfield Toon Addon",
    "author": "kkskaguya",
    "version": (4, 0, 2),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Endfield Toon",
    "description": "One-click convert imported materials to Arknights: Endfield toon shading.",
    "category": "Material",
}

import os
import re
from dataclasses import dataclass

import bpy
from bpy.app.handlers import persistent
from mathutils import Matrix, Vector
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, FloatProperty, IntProperty, PointerProperty, StringProperty
from bpy.types import Operator, Panel, PropertyGroup


BUNDLED_PRESET_NAME = "Chen.blend"


SHADER_TYPE_ITEMS = [
    ("BODY", "身体", ""),
    ("CLOTH", "衣服", ""),
    ("FACE", "脸部", ""),
    ("HAIR", "头发", ""),
    ("PUPIL", "眼部", ""),
]

SHADER_GROUP_KEYWORDS = {
    "BODY": ("Arknights: Endfield_PBRToonBase", "Arknights: Endfield_PBRToonBase2.0"),
    "CLOTH": ("Arknights: Endfield_PBRToonBase", "Arknights: Endfield_PBRToonBase2.0"),
    "FACE": ("Arknights: Endfield_PBRToonFaceBase", "Arknights: Endfield_PBRToonFaceBase2.0"),
    "HAIR": ("Arknights: Endfield_PBRToonBaseHair",),
    "PUPIL": ("Arknights: Endfield_PBRToon_irisBase", "Arknights: Endfield_PBRToon_irisBase2.0"),
    "BROW": ("Arknights: Endfield_PBRToonBaseBrow",),
}

TEMPLATE_MATERIAL_PREFS = {
    "BODY": [
        "M_actor_chen_body_01.001",
        "M_actor_chen_body_01.002",
        "M_actor_endminf_body_01",
        "M_actor_endminf_body_02",
    ],
    "CLOTH": [
        "M_actor_chen_cloth_01",
        "M_actor_chen_cloth_01.001",
        "M_actor_endminf_cloth_03",
        "M_actor_endminf_cloth_01",
        "M_actor_endminf_cloth_02",
        "M_actor_endminf_cloth_04",
    ],
    "FACE": [
        "M_actor_endminf_face_01",
        "M_actor_chen_face_01.002",
        "M_actor_chen_face_01.001",
    ],
    "HAIR": [
        "M_actor_endminf_hair_01",
        "M_actor_chen_hair_01.001",
    ],
    "PUPIL": [
        "M_actor_endminf_iris_01",
        "M_actor_chen_iris_01.002",
    ],
    "BROW": [
        "M_actor_endminf_brow_01",
        "M_actor_chen_brow_01.002",
    ],
}

ALPHA_TEMPLATE_PREFS = {
    "IRIS": [
        "M_actor_chen_iris_01.001Alpha.001",
        "M_actor_chen_iris_01.001Alpha",
    ],
    "BROW": [
        "M_actor_chen_brow_01.001Alpha.001",
        "M_actor_chen_brow_01.001Alpha",
    ],
}

OUTLINE_MATERIAL_PREFS = {
    "BODY": [
        "Chen_Cmmom_outline",
        "Endmin Cloth Outline",
        "FemEndmin outline",
        "Chen_Face_outline",
    ],
    "CLOTH": [
        "Chen_cloth_outline",
        "Endmin Cloth Outline",
        "FemEndmin outline",
        "Chen_Cmmom_outline",
        "Chen_Face_outline",
    ],
    "FACE": [
        "Chen_Face_outline",
        "FemEndmin outline",
        "Endmin Cloth Outline",
    ],
    "HAIR": [
        "PLK_hair_outline",
        "FemEndmin outline",
        "Chen_Face_outline",
    ],
    "PUPIL": [
        "Chen_Face_outline",
        "FemEndmin outline",
    ],
}

SPECIAL_MATERIAL_PREFS = {
    "SHADOW_PROXY": ["Only Shadow Proxy"],
}

GEOMETRY_NODE_PREFS = {
    "SUN_VEC": ["日光方向传递", "FemEndmin SunVec"],
    "SMOOTH_OUTLINE": ["平滑描边"],
    "FACE_VECTOR": ["脸方向向量"],
    "FACE_RAYCAST": ["光线投射"],
    "EYE_TRANSPARENCY": ["眼透位移"],
    "TIME_SETUP": ["鏃堕棿璁剧疆"],
    "SHADOW_PROXY": ["Shadow Proxy"],
}

SOURCE_MASTER_COLLECTION_NAME = "CHEN_MASTER"
SOURCE_RIG_COLLECTION_NAME = "CHEN_RIG"
SOURCE_MESH_COLLECTION_NAME = "CHEN MESH"
SOURCE_MESH_HIGH_COLLECTION_NAME = "CHEN_MESH HIGH POLY"
SOURCE_MESH_LOW_COLLECTION_NAME = "CHEN_MESH LOW POLY"
MASTER_COLLECTION_NAME = "FEMEND_MASTER"
RIG_COLLECTION_NAME = "FEMEND_RIG"
MESH_COLLECTION_NAME = "FEMEND_MESH"
MESH_HIGH_COLLECTION_NAME = "FEMEND_MESH HIGH POLY"
MESH_LOW_COLLECTION_NAME = "FEMEND_MESH LOW POLY"
HELPER_COLLECTION_NAME = "Do not touch"
SOURCE_UTILITY_COLLECTION_NAME = "CHEN_UTILITY"
SOURCE_WIDGETS_COLLECTION_NAME = "CHEN_Widgets"
SOURCE_META_COLLECTION_NAME = "CHEN_Meta"
UTILITY_COLLECTION_NAME = "UTILITY"
WIDGETS_COLLECTION_NAME = "Widgets"
META_COLLECTION_NAME = "Meta"
SOURCE_WORLD_NAME = "World"
TARGET_WORLD_NAME = "zmd world"
SOURCE_CAMERA_NAME = "摄像机"
SOURCE_SUN_LIGHT_NAME = "Chen Light"
SUN_LIGHT_NAME = "FEMEND Sun"
SUN_HELPER_LC_NAME = "LC"
SUN_HELPER_LF_NAME = "LF"
SOURCE_HEAD_HELPER_NAME = "Chen_HC"
SOURCE_HEAD_FORWARD_NAME = "Chen_HF"
SOURCE_HEAD_RIGHT_NAME = "Chen_HR"
HEAD_HELPER_NAME = "HC"
HEAD_FORWARD_NAME = "HF"
HEAD_RIGHT_NAME = "HR"
SUN_LIGHT_LOCATION = Vector((0.042163014, -0.305859387, 1.494289517))
SUN_LIGHT_ROTATION = Vector((-0.426414639, 1.021072388, -7.807478905))
SUN_LC_DISTANCE = 0.587259948
SUN_LF_DISTANCE = 1.329999924
HEAD_FORWARD_OFFSET = Vector((0.0, -0.27221608, 0.0))
HEAD_RIGHT_OFFSET = Vector((-0.27067417, 0.0, 0.0))
HEAD_HELPER_SCALE = (0.28153285, 0.28153285, 0.28153285)
HEAD_DIRECTION_SCALE = (0.19306129, 0.19306129, 0.19306129)
TEST_WELD_MODIFIER_NAME = "Endfield_TestWeld"
BODY_WELD_MODIFIER_NAME = "鐒婃帴"
BODY_WELD_DISTANCE = 0.0001
TEST_GN_MERGE_MODIFIER_NAME = "Endfield_TestGNMerge"
TEST_GN_MERGE_GROUP_NAME = "Endfield_TestMergeByDistance"
TEST_PROXY_SUFFIX = "_OutlineProxy"
TEST_PROXY_MATERIAL_NAME = "ENDFIELD_ProxyOutline"

HEAD_BONE_KEYWORDS = ("head", "头", "首")


HEAD_BONE_EXACT_NAMES = (
    "head",
    "Head",
    "HEAD",
    "Head.x",
    "head.x",
    "Bip001 Head",
    "bip001 head",
    "mixamorig:Head",
    "ValveBiped.Bip01_Head1",
    "J_Head",
    "j_head",
    "C_Head",
    "c_head",
    "Bone_Head",
    "bone_head",
)
HEAD_BONE_KEYWORDS = ("head", "face")
HEAD_BONE_EXCLUDE_KEYWORDS = ("twist", "end", "nub", "top", "look", "track", "aim", "ik", "socket")
LATTICE_BONE_PREFIXES = ("DEF-", "DEF_", "def-", "def_")
LATTICE_OBJECT_BASENAME = "Lattice"
LATTICE_FIT_MARGIN = Vector((1.15, 1.15, 1.15))

LEGACY_COLLECTION_NAME_PAIRS = (
    (SOURCE_MASTER_COLLECTION_NAME, MASTER_COLLECTION_NAME),
    (SOURCE_RIG_COLLECTION_NAME, RIG_COLLECTION_NAME),
    (SOURCE_MESH_COLLECTION_NAME, MESH_COLLECTION_NAME),
    (SOURCE_MESH_HIGH_COLLECTION_NAME, MESH_HIGH_COLLECTION_NAME),
    (SOURCE_MESH_LOW_COLLECTION_NAME, MESH_LOW_COLLECTION_NAME),
    (SOURCE_UTILITY_COLLECTION_NAME, UTILITY_COLLECTION_NAME),
    (SOURCE_WIDGETS_COLLECTION_NAME, WIDGETS_COLLECTION_NAME),
    (SOURCE_META_COLLECTION_NAME, META_COLLECTION_NAME),
)

LEGACY_OBJECT_NAME_PAIRS = (
    (SOURCE_SUN_LIGHT_NAME, SUN_LIGHT_NAME),
    (SOURCE_HEAD_HELPER_NAME, HEAD_HELPER_NAME),
    (SOURCE_HEAD_FORWARD_NAME, HEAD_FORWARD_NAME),
    (SOURCE_HEAD_RIGHT_NAME, HEAD_RIGHT_NAME),
)

@dataclass(frozen=True)
class TextureSlotDef:
    prop_id: str
    label: str
    colorspace: str = "sRGB"


TEXTURE_SLOT_LAYOUT = {
    "BODY": [
        TextureSlotDef("tex_d", "_D.png (BaseColor)", "sRGB"),
        TextureSlotDef("tex_n", "_N.png (Normal)", "Non-Color"),
        TextureSlotDef("tex_p", "_P.png / _ID.png (ILM)", "Non-Color"),
        TextureSlotDef("tex_m", "_M.png (Metal/Smooth)", "Non-Color"),
        TextureSlotDef("tex_st", "_ST.png (Outline Mask, Optional)", "Non-Color"),
        TextureSlotDef("tex_e", "_E.png (Emission, Optional)", "Non-Color"),
    ],
    "CLOTH": [
        TextureSlotDef("tex_d", "_D.png (BaseColor)", "sRGB"),
        TextureSlotDef("tex_n", "_N.png (Normal)", "Non-Color"),
        TextureSlotDef("tex_p", "_P.png / _ID.png (ILM)", "Non-Color"),
        TextureSlotDef("tex_m", "_M.png (Metal/Smooth)", "Non-Color"),
        TextureSlotDef("tex_st", "_ST.png (Outline Mask, Optional)", "Non-Color"),
        TextureSlotDef("tex_e", "_E.png (Emission, Optional)", "Non-Color"),
    ],
    "FACE": [
        TextureSlotDef("tex_d", "_D.png (Face Base)", "sRGB"),
        TextureSlotDef("tex_st", "_ST.png (Face SDF/Outline Mask, Optional)", "Non-Color"),
    ],
    "HAIR": [
        TextureSlotDef("tex_d", "_D.png (BaseColor)", "sRGB"),
        TextureSlotDef("tex_n", "_N.png / _HN.png (Hair Normal)", "Non-Color"),
        TextureSlotDef("tex_p", "_P.png / _ID.png (ILM)", "Non-Color"),
        TextureSlotDef("tex_st", "_ST.png (Hair Outline Mask, Optional)", "Non-Color"),
    ],
    "PUPIL": [
        TextureSlotDef("tex_d", "_D.png (Iris Base)", "sRGB"),
    ],
    "BROW": [
        TextureSlotDef("tex_d", "_D.png (Brow/Lash Base)", "sRGB"),
    ],
}

ROLE_SUFFIX_CANDIDATES = {
    "tex_n": ["_N", "_HN"],
    "tex_p": ["_P", "_ID", "_ILM", "_LightMap"],
    "tex_m": ["_M", "_ORM", "_RMA"],
    "tex_st": ["_ST"],
    "tex_e": ["_E", "_EM"],
}

ROLE_SEARCH_TAGS = {
    "tex_d": ["mmd_base_tex", "_d", "base color", "basecolor", "albedo", "d_rgb"],
    "tex_n": ["_n", "_hn", "normal", "娉曠嚎"],
    "tex_p": ["_p", "_id", "_ilm", "lightmap", "lm", "spec"],
    "tex_m": ["_m", "metal", "rough", "smooth", "orm", "rma"],
    "tex_st": ["_st", "stock", "outline", "mask", "sdf"],
    "tex_e": ["_e", "emi", "emission"],
}

ROLE_COLORSPACE_DEFAULTS = {
    "tex_d": "sRGB",
    "tex_n": "Non-Color",
    "tex_p": "Non-Color",
    "tex_m": "Non-Color",
    "tex_st": "Non-Color",
    "tex_e": "Non-Color",
}

ROLE_SOCKET_KEYWORDS = {
    "tex_d_color": ["_d(srgb)r.g.b"],
    "tex_d_alpha": ["_d(srgb).a"],
    "tex_n_color": ["_n(non_color)", "_hn(non_color)r.g.b", "_hn"],
    "tex_n_alpha": ["_hn(non_color)a", "_hn.a"],
    "tex_p_color": ["_p(non_color)r.g.b", "_p"],
    "tex_p_alpha": ["_p(non_color)a", "_p.a"],
    "tex_m_color": ["_m", "metal", "smooth", "rough"],
    "tex_e_color": ["_e", "emission", "emi"],
}

EYE_TRANSPARENCY_MODIFIER_PREFIX = "Eye Transparency"

SAFE_TWEAKS = {
    "BODY": [
        ("明暗分界", "CastShadow_center"),
        ("阴影锐度", "CastShadow_sharp"),
        ("边缘光宽度 X", "Rim_width_X"),
        ("边缘光宽度 Y", "Rim_width_Y"),
        ("边缘光强度", "Rim_ColorStrength"),
        ("全局阴影亮度", "GlobalShadowBrightnessAdjustment"),
    ],
    "CLOTH": [
        ("明暗分界", "CastShadow_center"),
        ("阴影锐度", "CastShadow_sharp"),
        ("边缘光宽度 X", "Rim_width_X"),
        ("边缘光宽度 Y", "Rim_width_Y"),
        ("边缘光强度", "Rim_ColorStrength"),
        ("全局阴影亮度", "GlobalShadowBrightnessAdjustment"),
    ],
    "FACE": [
        ("脸部SDF中心", "SDF_RemaphalfLambert_center"),
        ("脸部SDF锐度", "SDF_RemaphalfLambert_sharp"),
        ("正面高光强度", "Front R Pow"),
        ("正面高光平滑", "Front R Smo"),
        ("脸部整体亮度", "Face Final brightness"),
        ("全局阴影亮度", "GlobalShadowBrightnessAdjustment"),
    ],
    "HAIR": [
        ("头发明暗分界", "CastShadow_center"),
        ("头发阴影锐度", "CastShadow_sharp"),
        ("边缘光宽度", "Rim_width_X"),
        ("边缘光强度", "Rim_ColorStrength"),
        ("高光位置", "FHighLightPos"),
        ("最终亮度", "Final brightness"),
    ],
    "PUPIL": [
        ("瞳孔亮度", "Eyes brightness"),
        ("瞳孔高光亮度", "Eyes HightLight brightness"),
    ],
}


def _ensure_face_eye_material_slot_count(settings, iris_min: int = 1, brow_min: int = 1):
    while len(settings.face_iris_materials) < iris_min:
        settings.face_iris_materials.add()
    while len(settings.face_brow_materials) < brow_min:
        settings.face_brow_materials.add()


def _on_face_integrated_eye_update(self, context):
    if self.face_integrated_eye_transparency:
        _ensure_face_eye_material_slot_count(self, 1, 1)


def _poll_armature_object(self, obj):
    return bool(obj and obj.type == "ARMATURE")


class ENDFIELD_PG_FaceEyeMaterialSlot(PropertyGroup):
    source_material: PointerProperty(name="原材质", type=bpy.types.Material)


class ENDFIELD_PG_Settings(PropertyGroup):
    preset_library_path: StringProperty(
        name="预设库(.blend)",
        subtype="FILE_PATH",
        description="留空时默认使用插件内置的 Chen.blend",
    )
    shader_type: EnumProperty(name="着色器类型选择", items=SHADER_TYPE_ITEMS, default="BODY")
    apply_mode: EnumProperty(
        name="替换范围",
        items=[
            ("ACTIVE_SLOT", "当前材质槽", ""),
            ("ALL_SLOTS", "全部材质槽", ""),
        ],
        default="ACTIVE_SLOT",
    )
    apply_selected_objects: BoolProperty(name="作用于所选网格", default=True)
    auto_fill_missing_maps: BoolProperty(name="一键生成时自动补全缺失贴图", default=True)
    clear_custom_normals: BoolProperty(name="清理自定义分裂法线", default=False)
    force_slot2_outline: BoolProperty(name="保留/创建第2材质槽描边", default=True)
    create_helper_rig: BoolProperty(name="迁移辅助集合/空物体/光源", default=True)
    auto_geometry_nodes: BoolProperty(name="自动挂载几何节点", default=True)
    migrate_source_environment: BoolProperty(name="迁移World/场景环境", default=True)
    outline_modifier_name: StringProperty(name="描边修改器名", default="Endfield_Outline")
    outline_thickness: FloatProperty(name="描边厚度", default=0.001, min=0.0, precision=6, soft_max=0.02)
    outline_material_offset: IntProperty(name="描边材质偏移", default=31, min=0, max=1000)
    test_weld_distance: FloatProperty(name="Weld距离", default=0.0005, min=0.0, precision=6, soft_max=0.01)
    test_gn_merge_distance: FloatProperty(name="GN合并距离", default=0.0005, min=0.0, precision=6, soft_max=0.01)
    head_bone_armature: PointerProperty(
        name="头部骨架",
        type=bpy.types.Object,
        poll=_poll_armature_object,
        description="可手动指定用于头部辅助空物体与 Lattice 的骨架",
    )
    head_bone_name: StringProperty(
        name="头部骨骼",
        description="可手动指定头部骨骼；留空时自动识别常见 Head 骨骼",
        default="",
    )
    eye_target_object: PointerProperty(
        name="眼透位移目标",
        type=bpy.types.Object,
        description="手动指定挂载眼透位移几何节点的网格对象；留空则自动识别",
    )
    eye_target_name: StringProperty(
        name="眼透位移目标搜索",
        description="手动指定挂载眼透位移几何节点的网格对象名称；留空则自动识别",
        default="",
    )
    face_integrated_eye_transparency: BoolProperty(
        name="眼部与脸部一体",
        description="在脸部模式下，对同一对象中指定材质追加眼透位移；材质结构仍来自预设库",
        default=False,
        update=_on_face_integrated_eye_update,
    )
    face_iris_materials: CollectionProperty(type=ENDFIELD_PG_FaceEyeMaterialSlot)
    face_brow_materials: CollectionProperty(type=ENDFIELD_PG_FaceEyeMaterialSlot)

    tex_d: StringProperty(name="_D", subtype="FILE_PATH")
    tex_n: StringProperty(name="_N", subtype="FILE_PATH")
    tex_p: StringProperty(name="_P", subtype="FILE_PATH")
    tex_m: StringProperty(name="_M", subtype="FILE_PATH")
    tex_st: StringProperty(name="_ST", subtype="FILE_PATH")
    tex_e: StringProperty(name="_E", subtype="FILE_PATH")


def _safe_abs_path(path_value: str) -> str:
    if not path_value:
        return ""
    return bpy.path.abspath(path_value)


def _addon_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _bundled_library_path() -> str:
    candidate = os.path.join(_addon_dir(), "presets", BUNDLED_PRESET_NAME)
    return candidate if os.path.exists(candidate) else ""

def _effective_library_path(settings: ENDFIELD_PG_Settings) -> str:
    user_path = _safe_abs_path(getattr(settings, "preset_library_path", ""))
    if user_path and os.path.exists(user_path):
        return user_path
    return _bundled_library_path()


def _copy_rna_properties(src, dst, exclude_ids=None):
    exclude = set(exclude_ids or ())
    for prop in src.bl_rna.properties:
        prop_id = prop.identifier
        if prop_id == "rna_type" or prop_id in exclude:
            continue
        if getattr(prop, "is_readonly", False):
            continue
        try:
            setattr(dst, prop_id, getattr(src, prop_id))
        except Exception:
            continue


SOURCE_LIBRARY_STAMP_KEY = "_endfield_source_library_stamp"


def _library_stamp(library_path: str) -> str:
    if not library_path or not os.path.exists(library_path):
        return ""
    try:
        mtime = os.path.getmtime(library_path)
    except OSError:
        mtime = 0.0
    return f"{os.path.abspath(library_path)}|{mtime}"


def _name_matches_datablock(base_name: str, candidate_name: str) -> bool:
    return candidate_name == base_name or candidate_name.startswith(f"{base_name}.")


def _make_backup_name(data_collection, base_name: str, suffix: str) -> str:
    candidate = f"{base_name}{suffix}"
    existing_names = {item.name for item in data_collection}
    index = 1
    while candidate in existing_names:
        candidate = f"{base_name}{suffix}.{index:03d}"
        index += 1
    return candidate


def _append_datablock_from_library(library_path: str, collection_name: str, datablock_name: str):
    if not library_path or not os.path.exists(library_path):
        return None
    data_collection = getattr(bpy.data, collection_name)
    before_names = {item.name for item in data_collection}
    try:
        with bpy.data.libraries.load(library_path, link=False) as (data_from, data_to):
            available = getattr(data_from, collection_name)
            if datablock_name not in available:
                return None
            setattr(data_to, collection_name, [datablock_name])
        appended = None
        for item in data_collection:
            if not _name_matches_datablock(datablock_name, item.name):
                continue
            if item.name not in before_names:
                appended = item
                break
        if appended is not None:
            stamp = _library_stamp(library_path)
            if stamp:
                appended[SOURCE_LIBRARY_STAMP_KEY] = stamp
        return appended
    except Exception:
        return None


def _find_stamped_material(material_name: str, library_path: str):
    stamp = _library_stamp(library_path)
    if not stamp:
        return bpy.data.materials.get(material_name)
    for material in bpy.data.materials:
        if _name_matches_datablock(material_name, material.name) and material.get(SOURCE_LIBRARY_STAMP_KEY) == stamp:
            return material
    return None


def _stash_outdated_material(material_name: str, library_path: str):
    material = bpy.data.materials.get(material_name)
    stamp = _library_stamp(library_path)
    if material is None or not stamp:
        return
    if material.get(SOURCE_LIBRARY_STAMP_KEY) == stamp:
        return
    material.name = _make_backup_name(bpy.data.materials, material_name, "__OLD")


def _find_stamped_object(object_name: str, library_path: str):
    stamp = _library_stamp(library_path)
    if not stamp:
        return bpy.data.objects.get(object_name)
    for obj in bpy.data.objects:
        if _name_matches_datablock(object_name, obj.name) and obj.get(SOURCE_LIBRARY_STAMP_KEY) == stamp:
            return obj
    return None


def _stash_outdated_object(object_name: str, library_path: str):
    obj = bpy.data.objects.get(object_name)
    stamp = _library_stamp(library_path)
    if obj is None or not stamp:
        return
    if obj.get(SOURCE_LIBRARY_STAMP_KEY) == stamp:
        return
    obj.name = _make_backup_name(bpy.data.objects, object_name, "__OLD")


def _find_matching_object(object_name: str):
    obj = bpy.data.objects.get(object_name)
    if obj is not None:
        return obj
    for candidate in bpy.data.objects:
        if _name_matches_datablock(object_name, candidate.name):
            return candidate
    return None


def _find_matching_collection(collection_name: str):
    collection = bpy.data.collections.get(collection_name)
    if collection is not None:
        return collection
    for candidate in bpy.data.collections:
        if _name_matches_datablock(collection_name, candidate.name):
            return candidate
    return None


def _rename_datablock(datablocks, datablock, target_name: str):
    if datablock is None or not target_name or datablock.name == target_name:
        return datablock
    existing = datablocks.get(target_name)
    if existing is not None and existing != datablock:
        return existing
    datablock.name = target_name
    return datablock


def _ensure_object_alias(target_name: str, *aliases: str):
    obj = _find_matching_object(target_name)
    if obj is not None:
        return _rename_datablock(bpy.data.objects, obj, target_name)
    for alias in aliases:
        if not alias:
            continue
        obj = _find_matching_object(alias)
        if obj is not None:
            return _rename_datablock(bpy.data.objects, obj, target_name)
    return None


def _ensure_collection_alias(target_name: str, *aliases: str):
    collection = _find_matching_collection(target_name)
    if collection is not None:
        return _rename_datablock(bpy.data.collections, collection, target_name)
    for alias in aliases:
        if not alias:
            continue
        collection = _find_matching_collection(alias)
        if collection is not None:
            return _rename_datablock(bpy.data.collections, collection, target_name)
    return None


def _strip_scene_prefix(name: str):
    for prefix in ("CHEN_", "CHEN ", "Chen_", "Chen "):
        if name.startswith(prefix):
            return name[len(prefix):]
    return name


def _normalize_helper_collection_tree(helper_collection):
    if helper_collection is None:
        return
    stack = list(helper_collection.children)
    while stack:
        collection = stack.pop()
        stack.extend(list(collection.children))
        stripped_name = _strip_scene_prefix(collection.name)
        if stripped_name != collection.name:
            _rename_datablock(bpy.data.collections, collection, stripped_name)


def _normalize_legacy_scene_names():
    for source_name, target_name in LEGACY_COLLECTION_NAME_PAIRS:
        _ensure_collection_alias(target_name, source_name)
    for source_name, target_name in LEGACY_OBJECT_NAME_PAIRS:
        _ensure_object_alias(target_name, source_name)
    helper_collection = bpy.data.collections.get(HELPER_COLLECTION_NAME)
    if helper_collection is not None:
        _normalize_helper_collection_tree(helper_collection)


def _find_stamped_node_group(group_name: str, library_path: str, tree_type: str = None):
    stamp = _library_stamp(library_path)
    if not stamp:
        group = bpy.data.node_groups.get(group_name)
        if group and (tree_type is None or group.bl_idname == tree_type):
            return group
        return None
    for group in bpy.data.node_groups:
        if not _name_matches_datablock(group_name, group.name):
            continue
        if tree_type is not None and group.bl_idname != tree_type:
            continue
        if group.get(SOURCE_LIBRARY_STAMP_KEY) == stamp:
            return group
    return None


def _stash_outdated_node_group(group_name: str, library_path: str, tree_type: str = None):
    stamp = _library_stamp(library_path)
    if not stamp:
        return
    group = bpy.data.node_groups.get(group_name)
    if group is None:
        return
    if tree_type is not None and group.bl_idname != tree_type:
        return
    if group.get(SOURCE_LIBRARY_STAMP_KEY) == stamp:
        return
    group.name = _make_backup_name(bpy.data.node_groups, group_name, "__OLD")


def _find_or_append_node_group_by_name(library_path: str, group_name: str, tree_type: str = None):
    group = _find_stamped_node_group(group_name, library_path, tree_type=tree_type)
    if group:
        return group
    _stash_outdated_node_group(group_name, library_path, tree_type=tree_type)
    group = _append_datablock_from_library(library_path, "node_groups", group_name)
    if group and (tree_type is None or group.bl_idname == tree_type):
        return group
    group = bpy.data.node_groups.get(group_name)
    if group and (tree_type is None or group.bl_idname == tree_type):
        return group
    return None


def _ensure_node_tree_uses_library_groups(node_tree, library_path: str, visited=None):
    if not node_tree or not library_path:
        return node_tree
    if node_tree.get("_endfield_face_group_local"):
        return node_tree

    visited = visited or set()
    tree_key = node_tree.as_pointer()
    if tree_key in visited:
        return node_tree
    visited.add(tree_key)

    for node in node_tree.nodes:
        if node.type != "GROUP" or not node.node_tree:
            continue
        target_group = node.node_tree
        if not target_group.get("_endfield_face_group_local"):
            rebound_group = _find_or_append_node_group_by_name(
                library_path,
                target_group.name,
                tree_type=target_group.bl_idname,
            )
            if rebound_group is not None:
                target_group = rebound_group
                if node.node_tree != rebound_group:
                    node.node_tree = rebound_group
        _ensure_node_tree_uses_library_groups(target_group, library_path, visited)

    return node_tree


def _ensure_material_uses_library_node_groups(material, library_path: str):
    if not material or not material.use_nodes or not material.node_tree:
        return material
    _ensure_node_tree_uses_library_groups(material.node_tree, library_path)
    return material


def _find_or_append_material_by_name(library_path: str, material_name: str):
    material = _find_stamped_material(material_name, library_path)
    if material:
        return _ensure_material_uses_library_node_groups(material, library_path)
    _stash_outdated_material(material_name, library_path)
    material = _append_datablock_from_library(library_path, "materials", material_name)
    if material:
        return _ensure_material_uses_library_node_groups(material, library_path)
    material = bpy.data.materials.get(material_name)
    if material:
        return _ensure_material_uses_library_node_groups(material, library_path)
    return None


def _find_stamped_world(world_name: str, library_path: str):
    stamp = _library_stamp(library_path)
    if not stamp:
        return bpy.data.worlds.get(world_name)
    for world in bpy.data.worlds:
        if _name_matches_datablock(world_name, world.name) and world.get(SOURCE_LIBRARY_STAMP_KEY) == stamp:
            return world
    return None


def _stash_outdated_world(world_name: str, library_path: str):
    world = bpy.data.worlds.get(world_name)
    stamp = _library_stamp(library_path)
    if world is None or not stamp:
        return
    if world.get(SOURCE_LIBRARY_STAMP_KEY) == stamp:
        return
    world.name = _make_backup_name(bpy.data.worlds, world_name, "__OLD")


def _find_or_append_first_material(library_path: str, candidates):
    for name in candidates:
        material = _find_or_append_material_by_name(library_path, name)
        if material:
            return material
    return None


def _prime_preset_resources(settings: ENDFIELD_PG_Settings):
    library = _effective_library_path(settings)
    if not library:
        return False

    material_names = []
    seen = set()
    for candidate_group in (
        TEMPLATE_MATERIAL_PREFS.values(),
        ALPHA_TEMPLATE_PREFS.values(),
        OUTLINE_MATERIAL_PREFS.values(),
        SPECIAL_MATERIAL_PREFS.values(),
    ):
        for names in candidate_group:
            for name in names:
                if name in seen:
                    continue
                seen.add(name)
                material_names.append(name)

    for material_name in material_names:
        _find_or_append_material_by_name(library, material_name)

    for group_names in GEOMETRY_NODE_PREFS.values():
        _find_or_append_node_group(library, group_names)

    if settings.migrate_source_environment:
        _ensure_target_world(settings)
    if settings.shader_type == "FACE" and (settings.create_helper_rig or settings.auto_geometry_nodes):
        _ensure_sun_rig(settings)
    return True


def _find_or_append_node_group(library_path: str, candidates):
    for group_name in candidates:
        group = _find_or_append_node_group_by_name(library_path, group_name, tree_type="GeometryNodeTree")
        if group:
            return group
    return None


def _find_or_append_collection(library_path: str, collection_name: str):
    collection = bpy.data.collections.get(collection_name)
    if collection:
        return collection
    if _append_datablock_from_library(library_path, "collections", collection_name):
        return bpy.data.collections.get(collection_name)
    return None


def _find_or_append_object(library_path: str, object_name: str):
    obj = _find_stamped_object(object_name, library_path)
    if obj:
        return obj
    _stash_outdated_object(object_name, library_path)
    obj = _append_datablock_from_library(library_path, "objects", object_name)
    if obj:
        return obj
    return _find_matching_object(object_name)


def _find_or_append_world(library_path: str, world_name: str = SOURCE_WORLD_NAME):
    world = _find_stamped_world(world_name, library_path)
    if world:
        return world
    _stash_outdated_world(world_name, library_path)
    world = _append_datablock_from_library(library_path, "worlds", world_name)
    if world:
        return world
    world = bpy.data.worlds.get(world_name)
    if world:
        return world
    return bpy.data.worlds[0] if bpy.data.worlds else None


def _ensure_target_world(settings: ENDFIELD_PG_Settings):
    library = _effective_library_path(settings)
    if not library:
        return None

    expected_stamp = _library_stamp(library)
    existing = bpy.data.worlds.get(TARGET_WORLD_NAME)
    if existing is not None:
        if not expected_stamp or existing.get(SOURCE_LIBRARY_STAMP_KEY) == expected_stamp:
            return existing
        existing.name = _make_backup_name(bpy.data.worlds, TARGET_WORLD_NAME, "__OLD")

    source_world = _find_or_append_world(library)
    if source_world is None:
        return None

    if source_world.name != TARGET_WORLD_NAME:
        source_world.name = TARGET_WORLD_NAME
    if expected_stamp:
        source_world[SOURCE_LIBRARY_STAMP_KEY] = expected_stamp
    return source_world


def _cleanup_unused_world_backups():
    for world in list(bpy.data.worlds):
        if world.name.startswith(f"{SOURCE_WORLD_NAME}__OLD") and world.users == 0:
            bpy.data.worlds.remove(world)


def _create_fallback_material(name: str):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "mmd_base_tex"
    tex.label = "Mmd Base Tex"
    tex.location = (-520.0, 120.0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (-170.0, 120.0)
    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (120.0, 120.0)

    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return material


def _create_fallback_alpha_material(name: str):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "mmd_base_tex"
    tex.location = (-420.0, 120.0)
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    transparent.location = (-160.0, 20.0)
    mix = nodes.new("ShaderNodeMixShader")
    mix.location = (80.0, 100.0)
    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (300.0, 100.0)

    links.new(tex.outputs["Alpha"], mix.inputs["Fac"])
    links.new(transparent.outputs["BSDF"], mix.inputs[1])
    links.new(transparent.outputs["BSDF"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])
    _set_alpha_blend_mode(material)
    return material


def _create_shadow_proxy_material():
    material = bpy.data.materials.new("Only Shadow Proxy")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    holdout = nodes.new("ShaderNodeHoldout")
    holdout.location = (-80.0, 60.0)
    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (120.0, 60.0)
    links.new(holdout.outputs["Holdout"], out.inputs["Surface"])
    return material


def _create_fallback_outline_material(name: str):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "mmd_base_tex"
    tex.label = "Outline Base"
    tex.location = (-860.0, 180.0)

    diffuse = nodes.new("ShaderNodeBsdfDiffuse")
    diffuse.location = (-620.0, -60.0)

    shader_to_rgb = nodes.new("ShaderNodeShaderToRGB")
    shader_to_rgb.location = (-380.0, -60.0)

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.location = (-140.0, -60.0)
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[1].position = 0.7

    rgb_to_bw = nodes.new("ShaderNodeRGBToBW")
    rgb_to_bw.location = (20.0, -60.0)

    mix_rgb = nodes.new("ShaderNodeMixRGB")
    mix_rgb.location = (220.0, 140.0)
    mix_rgb.blend_type = "MIX"
    mix_rgb.inputs["Color2"].default_value = (0.02, 0.02, 0.02, 1.0)

    emission = nodes.new("ShaderNodeEmission")
    emission.location = (460.0, 140.0)

    transparent = nodes.new("ShaderNodeBsdfTransparent")
    transparent.location = (460.0, -60.0)

    mix_shader = nodes.new("ShaderNodeMixShader")
    mix_shader.location = (720.0, 100.0)

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (960.0, 100.0)

    links.new(tex.outputs["Color"], diffuse.inputs["Color"])
    links.new(diffuse.outputs["BSDF"], shader_to_rgb.inputs["Shader"])
    links.new(shader_to_rgb.outputs["Color"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], rgb_to_bw.inputs["Color"])
    links.new(rgb_to_bw.outputs["Val"], mix_rgb.inputs["Fac"])
    links.new(tex.outputs["Color"], mix_rgb.inputs["Color1"])
    links.new(mix_rgb.outputs["Color"], emission.inputs["Color"])
    links.new(tex.outputs["Alpha"], mix_shader.inputs["Fac"])
    links.new(transparent.outputs["BSDF"], mix_shader.inputs[1])
    links.new(emission.outputs["Emission"], mix_shader.inputs[2])
    links.new(mix_shader.outputs["Shader"], out.inputs["Surface"])

    _set_alpha_blend_mode(material)
    if hasattr(material, "use_backface_culling"):
        material.use_backface_culling = True
    return material


def _outline_material_candidates(settings: ENDFIELD_PG_Settings, obj=None, base_material=None):
    if settings.shader_type == "BODY":
        return ["Chen_Cmmom_outline", "Endmin Cloth Outline", "FemEndmin outline", "Chen_Face_outline"]
    if settings.shader_type == "CLOTH":
        return ["Chen_cloth_outline", "Endmin Cloth Outline", "FemEndmin outline", "Chen_Cmmom_outline", "Chen_Face_outline"]
    return list(OUTLINE_MATERIAL_PREFS[settings.shader_type])


def _is_lash_or_brow_target(obj=None, source_material=None) -> bool:
    keywords = ("brow", "lash", "eyelash", "眉", "睫")
    names = []
    if obj is not None:
        names.append(obj.name.lower())
    if source_material is not None:
        names.append(source_material.name.lower())
        shader_type = _detect_shader_type_from_material(source_material)
        if shader_type == "BROW":
            return True
    return any(any(keyword in name for keyword in keywords) for name in names)


def _template_material_candidates(shader_type: str, obj=None, source_material=None):
    if shader_type == "PUPIL" and _is_lash_or_brow_target(obj, source_material):
        return list(TEMPLATE_MATERIAL_PREFS["BROW"])
    return list(TEMPLATE_MATERIAL_PREFS[shader_type])


def _ensure_template_material(settings: ENDFIELD_PG_Settings, shader_type: str = None, obj=None, source_material=None):
    shader_type = shader_type or settings.shader_type
    resolved_shader_type = "BROW" if shader_type == "PUPIL" and _is_lash_or_brow_target(obj, source_material) else shader_type
    library = _effective_library_path(settings)
    material = _find_or_append_first_material(library, _template_material_candidates(resolved_shader_type, obj, source_material))
    if material:
        return material
    fallback_name = f"ENDFIELD_{resolved_shader_type}_Fallback"
    existing = bpy.data.materials.get(fallback_name)
    return existing or _create_fallback_material(fallback_name)


def _ensure_outline_material(settings: ENDFIELD_PG_Settings, obj=None, base_material=None):
    library = _effective_library_path(settings)
    material = _find_or_append_first_material(library, _outline_material_candidates(settings, obj, base_material))
    if material:
        if hasattr(material, "use_backface_culling"):
            material.use_backface_culling = True
        return material

    material = bpy.data.materials.get("ENDFIELD_Outline")
    if material:
        return material

    return _create_fallback_outline_material("ENDFIELD_Outline")


def _ensure_shadow_proxy_material(settings: ENDFIELD_PG_Settings):
    library = _effective_library_path(settings)
    material = _find_or_append_first_material(library, SPECIAL_MATERIAL_PREFS["SHADOW_PROXY"])
    if material:
        return material
    existing = bpy.data.materials.get("Only Shadow Proxy")
    return existing or _create_shadow_proxy_material()


def _set_alpha_blend_mode(material):
    try:
        material.blend_method = "HASHED"
    except Exception:
        pass
    if hasattr(material, "surface_render_method"):
        for mode in ("DITHERED", "BLENDED"):
            try:
                material.surface_render_method = mode
                break
            except Exception:
                continue
    if hasattr(material, "use_backface_culling"):
        material.use_backface_culling = True


def _load_image(path_value: str, colorspace: str):
    abs_path = _safe_abs_path(path_value)
    if not abs_path or not os.path.exists(abs_path):
        return None
    try:
        image = bpy.data.images.load(abs_path, check_existing=True)
    except RuntimeError:
        return None
    try:
        image.colorspace_settings.name = colorspace
    except Exception:
        pass
    return image


def _placeholder_rgba_for_role(role_id: str):
    if role_id == "tex_n":
        return (0.5, 0.5, 1.0, 1.0)
    if role_id == "tex_d":
        return (0.8, 0.8, 0.8, 1.0)
    return (0.0, 0.0, 0.0, 1.0)


def _ensure_placeholder_image(role_id: str, colorspace: str = None):
    colorspace = colorspace or ROLE_COLORSPACE_DEFAULTS.get(role_id, "Non-Color")
    safe_colorspace = re.sub(r"[^0-9A-Za-z]+", "_", colorspace).strip("_") or "Default"
    image_name = f"ENDFIELD_EMPTY_{role_id.upper()}_{safe_colorspace}"
    image = bpy.data.images.get(image_name)
    if image is None:
        image = bpy.data.images.new(image_name, width=1, height=1, alpha=True)
    try:
        image.generated_color = _placeholder_rgba_for_role(role_id)
    except Exception:
        pass
    try:
        image.colorspace_settings.name = colorspace
    except Exception:
        pass
    image["endfield_placeholder"] = True
    image["endfield_role_id"] = role_id
    return image


def _iter_tex_image_nodes(material):
    if not material or not material.use_nodes or not material.node_tree:
        return []
    return [node for node in material.node_tree.nodes if node.type == "TEX_IMAGE"]


def _node_signature(node) -> str:
    parts = [node.name.lower(), node.label.lower()]
    image = getattr(node, "image", None)
    if image and not image.get("endfield_placeholder"):
        parts.append(image.name.lower())
        if image.filepath:
            parts.append(image.filepath.lower())
    return " ".join(parts)


def _find_nodes_for_role(material, role_id: str):
    if not material or not material.use_nodes or not material.node_tree:
        return []

    found = []
    seen = set()

    def add_node(node):
        if not node or node.type != "TEX_IMAGE":
            return
        key = getattr(node, "name_full", node.name)
        if key in seen:
            return
        seen.add(key)
        found.append(node)

    sockets = _shader_input_sockets_for_role(material, role_id)
    if sockets:
        for socket in sockets.values():
            if not socket or not socket.is_linked:
                continue
            for link in socket.links:
                source_node = getattr(link.from_socket, "node", None)
                if source_node and source_node.type == "TEX_IMAGE":
                    add_node(source_node)

    if found:
        return found

    tags = ROLE_SEARCH_TAGS.get(role_id, [])
    for node in _iter_tex_image_nodes(material):
        text = _node_signature(node)
        if any(tag in text for tag in tags):
            add_node(node)
    return found


def _main_shader_group_node(material):
    try:
        return _find_main_shader_node(material)
    except Exception:
        return None


def _shader_input_sockets_for_role(material, role_id: str):
    group_node = _main_shader_group_node(material)
    if group_node is None:
        return {}

    def matches(socket_name: str, keywords):
        name = socket_name.lower()
        return any(keyword in name for keyword in keywords)

    inputs = {}
    for socket in group_node.inputs:
        if role_id == "tex_d":
            if matches(socket.name, ROLE_SOCKET_KEYWORDS["tex_d_color"]):
                inputs["color"] = socket
            elif matches(socket.name, ROLE_SOCKET_KEYWORDS["tex_d_alpha"]):
                inputs["alpha"] = socket
        elif role_id == "tex_n":
            if matches(socket.name, ROLE_SOCKET_KEYWORDS["tex_n_color"]):
                inputs["color"] = socket
            elif matches(socket.name, ROLE_SOCKET_KEYWORDS["tex_n_alpha"]):
                inputs["alpha"] = socket
        elif role_id == "tex_p":
            if matches(socket.name, ROLE_SOCKET_KEYWORDS["tex_p_color"]):
                inputs["color"] = socket
            elif matches(socket.name, ROLE_SOCKET_KEYWORDS["tex_p_alpha"]):
                inputs["alpha"] = socket
        elif role_id == "tex_m":
            if matches(socket.name, ROLE_SOCKET_KEYWORDS["tex_m_color"]):
                inputs["color"] = socket
        elif role_id == "tex_e":
            if matches(socket.name, ROLE_SOCKET_KEYWORDS["tex_e_color"]):
                inputs["color"] = socket
    return inputs


def _create_linked_role_node(material, role_id: str):
    if not material.use_nodes or not material.node_tree:
        return None
    sockets = _shader_input_sockets_for_role(material, role_id)
    if not sockets:
        return None

    node = material.node_tree.nodes.new("ShaderNodeTexImage")
    node.name = role_id
    node.label = role_id
    node.location = (-980.0, -220.0 - 120.0 * len(_iter_tex_image_nodes(material)))
    links = material.node_tree.links
    if "color" in sockets:
        links.new(node.outputs["Color"], sockets["color"])
    if "alpha" in sockets:
        links.new(node.outputs["Alpha"], sockets["alpha"])
    return node


def _find_or_create_nodes_for_role(material, role_id: str):
    found = _find_nodes_for_role(material, role_id)
    if found:
        return found
    created = _create_linked_role_node(material, role_id)
    if created is not None:
        return [created]
    return []


def _node_matches_role(node, role_id: str) -> bool:
    return any(tag in _node_signature(node) for tag in ROLE_SEARCH_TAGS.get(role_id, []))


def _assign_image_to_role_nodes(material, role_id: str, image, assigned_names, fallback_position: str = ""):
    nodes = [node for node in _find_nodes_for_role(material, role_id) if node.name not in assigned_names]
    if not nodes:
        free_nodes = [node for node in _iter_tex_image_nodes(material) if node.name not in assigned_names]
        if free_nodes:
            if fallback_position == "last":
                nodes = [free_nodes[-1]]
            elif fallback_position == "first":
                nodes = [free_nodes[0]]
    for node in nodes:
        node.image = image
        assigned_names.add(node.name)


def _rebind_outline_material_textures(material, loaded_images):
    if not material or not material.use_nodes or not material.node_tree:
        return

    assigned_names = set()
    tex_d_image = loaded_images.get("tex_d") or _ensure_placeholder_image("tex_d", ROLE_COLORSPACE_DEFAULTS["tex_d"])
    tex_st_image = loaded_images.get("tex_st") or _ensure_placeholder_image("tex_st", ROLE_COLORSPACE_DEFAULTS["tex_st"])
    _assign_image_to_role_nodes(material, "tex_d", tex_d_image, assigned_names, fallback_position="first")
    _assign_image_to_role_nodes(material, "tex_st", tex_st_image, assigned_names, fallback_position="last")

    if tex_d_image and not assigned_names:
        tex_nodes = _iter_tex_image_nodes(material)
        if tex_nodes:
            tex_nodes[0].image = tex_d_image
            assigned_names.add(tex_nodes[0].name)

    for node in _iter_tex_image_nodes(material):
        if node.name in assigned_names:
            continue
        if _node_matches_role(node, "tex_st"):
            node.image = tex_st_image
            assigned_names.add(node.name)
            continue
        if _node_matches_role(node, "tex_d"):
            node.image = tex_d_image
            assigned_names.add(node.name)

    _ensure_alpha_links(material)
    if _has_alpha(loaded_images.get("tex_d"), material.name):
        _set_alpha_blend_mode(material)


def _load_images_from_settings(settings: ENDFIELD_PG_Settings):
    loaded = {}
    for slot in TEXTURE_SLOT_LAYOUT[settings.shader_type]:
        image = _load_image(getattr(settings, slot.prop_id), slot.colorspace)
        if image:
            loaded[slot.prop_id] = image
    return loaded


def _eye_object_prefers_brow_material(obj, source_material=None) -> bool:
    keywords = ("brow", "lash", "eyelash", "眉", "睫")

    def has_keywords(text: str) -> bool:
        text = (text or "").lower()
        return any(keyword in text for keyword in keywords)

    if obj and has_keywords(obj.name):
        return True

    if source_material and has_keywords(source_material.name):
        return True

    if obj:
        for slot in obj.material_slots:
            material = slot.material
            if material and has_keywords(material.name):
                return True

    return False


def _shader_type_for_object(settings: ENDFIELD_PG_Settings, obj, source_material=None) -> str:
    shader_type = settings.shader_type
    if shader_type == "FACE" and settings.face_integrated_eye_transparency and source_material is not None:
        for item in settings.face_iris_materials:
            if item.source_material == source_material:
                return "PUPIL"
        for item in settings.face_brow_materials:
            if item.source_material == source_material:
                return "BROW"
    if shader_type == "PUPIL" and _eye_object_prefers_brow_material(obj, source_material):
        return "BROW"
    return shader_type


def _extract_loaded_images_from_material(material, shader_type: str):
    loaded = {}
    if not material:
        return loaded

    for slot in TEXTURE_SLOT_LAYOUT.get(shader_type, []):
        for node in _find_nodes_for_role(material, slot.prop_id):
            image = getattr(node, "image", None)
            if _image_is_usable(image):
                loaded[slot.prop_id] = image
                break

    if "tex_d" not in loaded:
        for node in _iter_tex_image_nodes(material):
            image = getattr(node, "image", None)
            if _image_is_usable(image):
                loaded["tex_d"] = image
                break

    return loaded


def _apply_source_material_images(target_material, source_material, shader_type: str):
    loaded = _extract_loaded_images_from_material(source_material, shader_type)
    image = loaded.get("tex_d")
    if image is None:
        for node in _iter_tex_image_nodes(source_material):
            candidate = getattr(node, "image", None)
            if _image_is_usable(candidate):
                image = candidate
                break

    role_presence = {}
    if image is not None:
        loaded["tex_d"] = image
        role_presence["tex_d"] = True
    else:
        image = _ensure_placeholder_image("tex_d", "sRGB")
        role_presence["tex_d"] = False

    for node in _find_or_create_nodes_for_role(target_material, "tex_d"):
        node.image = image

    _ensure_alpha_links(target_material)
    return loaded, role_presence


def _ensure_outline_material_instance(
    settings: ENDFIELD_PG_Settings,
    obj,
    base_material,
    loaded_images,
    name_override: str = "",
):
    template = _ensure_outline_material(settings, obj, base_material)
    material_name = name_override or f"{template.name}_{obj.name}_Outline"
    material = bpy.data.materials.get(material_name)
    if material is None:
        material = template.copy()
        material.name = material_name

    _rebind_outline_material_textures(material, loaded_images)
    if hasattr(material, "use_backface_culling"):
        material.use_backface_culling = True
    return material


def _ensure_alpha_links(material):
    if not material.use_nodes or not material.node_tree:
        return
    base_nodes = _find_nodes_for_role(material, "tex_d")
    if not base_nodes:
        return
    alpha_output = base_nodes[0].outputs.get("Alpha")
    if not alpha_output:
        return

    nodes = material.node_tree.nodes
    links = material.node_tree.links
    for node in nodes:
        if node.type == "GROUP":
            for socket_name in ("透明度", "Alpha", "D_Alpha", "_D(sRGB).A"):
                socket = node.inputs.get(socket_name)
                if socket and not socket.is_linked:
                    links.new(alpha_output, socket)
        if node.type == "BSDF_PRINCIPLED" and not node.inputs["Alpha"].is_linked:
            links.new(alpha_output, node.inputs["Alpha"])


def _has_alpha(image, material_name: str) -> bool:
    if "alpha" in material_name.lower():
        return True
    if not image:
        return False
    if "alpha" in image.name.lower():
        return True
    try:
        return image.channels >= 4
    except Exception:
        return False


def _image_is_usable(image) -> bool:
    if image is None:
        return False
    try:
        if image.get("endfield_placeholder"):
            return False
    except Exception:
        pass
    if getattr(image, "packed_file", None) is not None:
        return True
    filepath = bpy.path.abspath(image.filepath) if image.filepath else ""
    return bool(filepath and os.path.exists(filepath))


def _role_has_usable_image(material, role_id: str) -> bool:
    for node in _find_nodes_for_role(material, role_id):
        if _image_is_usable(getattr(node, "image", None)):
            return True
    return False


def _apply_textures(material, settings: ENDFIELD_PG_Settings, shader_type: str = None):
    shader_type = shader_type or settings.shader_type
    loaded = {}
    role_presence = {}

    for slot in TEXTURE_SLOT_LAYOUT[shader_type]:
        image = _load_image(getattr(settings, slot.prop_id), slot.colorspace)
        if image:
            loaded[slot.prop_id] = image
        else:
            image = _ensure_placeholder_image(slot.prop_id, slot.colorspace)
        for node in _find_or_create_nodes_for_role(material, slot.prop_id):
            node.image = image

    _ensure_alpha_links(material)
    if _has_alpha(loaded.get("tex_d"), material.name):
        shader_type = _detect_shader_type_from_material(material) or settings.shader_type
        if shader_type not in {"PUPIL", "BROW"}:
            _set_alpha_blend_mode(material)

    for slot in TEXTURE_SLOT_LAYOUT[shader_type]:
        role_presence[slot.prop_id] = _role_has_usable_image(material, slot.prop_id)

    return loaded, role_presence


def _ensure_second_outline_slot(obj, outline_material, force_assign: bool):
    for index, slot in enumerate(obj.material_slots):
        if _is_outline_like(slot.material):
            obj.material_slots[index].material = outline_material
            return index

    if force_assign and len(obj.material_slots) < 2:
        while len(obj.material_slots) < 2:
            obj.data.materials.append(None)
        obj.material_slots[1].material = outline_material
        return 1

    obj.data.materials.append(outline_material)
    return len(obj.material_slots) - 1


def _ensure_hair_auxiliary_slots(obj, settings: ENDFIELD_PG_Settings, outline_material):
    shadow_proxy = _ensure_shadow_proxy_material(settings)

    shadow_index = None
    outline_index = None
    for index, slot in enumerate(obj.material_slots):
        material = slot.material
        if material == shadow_proxy or (material and material.name.lower() == shadow_proxy.name.lower()):
            shadow_index = index
        elif material and _is_outline_like(material):
            outline_index = index

    if shadow_index is None:
        obj.data.materials.append(shadow_proxy)
        shadow_index = len(obj.material_slots) - 1
    else:
        obj.material_slots[shadow_index].material = shadow_proxy

    if outline_index is None:
        obj.data.materials.append(outline_material)
        outline_index = len(obj.material_slots) - 1
    else:
        obj.material_slots[outline_index].material = outline_material

    return shadow_index, outline_index


def _ensure_outline_modifier(obj, settings: ENDFIELD_PG_Settings):
    modifier = None
    for item in obj.modifiers:
        if item.type == "SOLIDIFY" or "outline" in item.name.lower():
            modifier = item
            break
    if modifier is None:
        modifier = obj.modifiers.new(settings.outline_modifier_name, "SOLIDIFY")
    modifier.name = settings.outline_modifier_name
    modifier.thickness = settings.outline_thickness
    if hasattr(modifier, "offset"):
        modifier.offset = 1.0
    modifier.material_offset = settings.outline_material_offset
    if hasattr(modifier, "use_flip_normals"):
        modifier.use_flip_normals = True
    if hasattr(modifier, "use_rim_only"):
        modifier.use_rim_only = False
    if hasattr(modifier, "use_rim"):
        modifier.use_rim = False
    return modifier


def _attach_geo_modifier(obj, node_group, name: str):
    modifier = None
    for item in obj.modifiers:
        if item.type == "NODES" and (item.name == name or item.node_group == node_group):
            modifier = item
            break
    if modifier is None:
        modifier = obj.modifiers.new(name, "NODES")
    modifier.name = name
    modifier.node_group = node_group
    return modifier


def _resolve_modifier_input_identifier(modifier, query: str):
    if not modifier or not modifier.node_group:
        return None
    if query in modifier.keys():
        return query
    for item in modifier.node_group.interface.items_tree:
        if item.item_type != "SOCKET" or item.in_out != "INPUT":
            continue
        if item.identifier == query or item.name == query:
            return item.identifier
    return None


def _set_modifier_input(modifier, query: str, value):
    identifier = _resolve_modifier_input_identifier(modifier, query)
    if not identifier:
        return False
    try:
        modifier[identifier] = value
        return True
    except Exception:
        return False


def _clear_custom_split_normals(context, obj):
    mesh = obj.data
    if not getattr(mesh, "has_custom_normals", False):
        return
    view_layer = context.view_layer
    prev_active = view_layer.objects.active
    prev_selected = [item for item in context.selected_objects]
    try:
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        view_layer.objects.active = obj
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="EDIT")
        if bpy.ops.mesh.select_all.poll():
            bpy.ops.mesh.select_all(action="SELECT")
        if bpy.ops.mesh.customdata_custom_splitnormals_clear.poll():
            bpy.ops.mesh.customdata_custom_splitnormals_clear()
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT")
    except Exception:
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT")
    finally:
        bpy.ops.object.select_all(action="DESELECT")
        for selected in prev_selected:
            if selected and selected.name in bpy.data.objects:
                selected.select_set(True)
        if prev_active and prev_active.name in bpy.data.objects:
            view_layer.objects.active = prev_active


def _set_shade_smooth(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = True


def _ensure_uv0_attribute(obj):
    mesh = obj.data
    uv_layers = getattr(mesh, "uv_layers", None)
    source_layer = None
    if uv_layers:
        source_layer = uv_layers.get("UV0") or getattr(uv_layers, "active", None) or (uv_layers[0] if len(uv_layers) else None)

    attr = mesh.attributes.get("UV0")
    if attr is None:
        attr = mesh.attributes.new("UV0", "FLOAT2", "CORNER")
    if source_layer is None:
        for item in attr.data:
            item.vector = (0.0, 0.0)
        return
    for item, uv in zip(attr.data, source_layer.data):
        item.vector = tuple(uv.uv)


def _ensure_white_color_attribute(obj, domain: str):
    mesh = obj.data
    attr = mesh.attributes.get("Color")
    if attr is None or attr.domain != domain or attr.data_type != "BYTE_COLOR":
        if attr is not None:
            try:
                mesh.attributes.remove(attr)
            except Exception:
                pass
        attr = mesh.color_attributes.new("Color", "BYTE_COLOR", domain)
    for item in attr.data:
        item.color = (1.0, 1.0, 1.0, 1.0)


def _ensure_smoothnormal_attribute(obj):
    mesh = obj.data
    attr = mesh.attributes.get("smoothnormalWS")
    if attr is None:
        attr = mesh.attributes.new("smoothnormalWS", "FLOAT_VECTOR", "CORNER")
    try:
        mesh.calc_normals_split()
    except Exception:
        pass
    corner_normals = getattr(mesh, "corner_normals", None)
    if corner_normals and len(corner_normals) == len(attr.data):
        for item, normal in zip(attr.data, corner_normals):
            vector = getattr(normal, "vector", normal)
            item.vector = tuple(vector)
        return
    for loop, item in zip(mesh.loops, attr.data):
        item.vector = tuple(loop.normal)


def _ensure_required_geometry_attributes(obj, shader_type: str):
    if obj is None or obj.type != "MESH":
        return
    _ensure_uv0_attribute(obj)
    _ensure_smoothnormal_attribute(obj)
    if shader_type == "HAIR":
        _ensure_white_color_attribute(obj, "CORNER")
    elif shader_type == "FACE":
        _ensure_white_color_attribute(obj, "POINT")


def _derive_texture_path(base_path: str, suffix: str) -> str:
    abs_path = _safe_abs_path(base_path)
    if not abs_path:
        return ""
    folder, filename = os.path.split(abs_path)
    stem, ext = os.path.splitext(filename)
    replaced = re.sub(r"(_[Dd])$", suffix, stem)
    if replaced == stem:
        replaced = stem + suffix
    candidate = os.path.join(folder, replaced + ext)
    return candidate if os.path.exists(candidate) else ""


def _guess_texture_by_scan(base_path: str, role_id: str) -> str:
    abs_path = _safe_abs_path(base_path)
    if not abs_path:
        return ""
    folder, filename = os.path.split(abs_path)
    stem, ext = os.path.splitext(filename)
    prefix = stem.rsplit("_", 1)[0] if "_" in stem else stem
    if not os.path.isdir(folder):
        return ""

    valid_ext = {".png", ".tga", ".jpg", ".jpeg", ".bmp", ".webp", ".dds", ext.lower()}
    keywords = ROLE_SEARCH_TAGS.get(role_id, [])
    for entry in os.listdir(folder):
        entry_lower = entry.lower()
        full = os.path.join(folder, entry)
        if not os.path.isfile(full):
            continue
        if os.path.splitext(entry)[1].lower() not in valid_ext:
            continue
        if prefix.lower() not in entry_lower:
            continue
        if any(tag in entry_lower for tag in keywords):
            return full
    return ""


def _autofill_missing_texture_paths(settings: ENDFIELD_PG_Settings) -> int:
    if not settings.tex_d:
        return 0

    filled = 0
    required_roles = {slot.prop_id for slot in TEXTURE_SLOT_LAYOUT[settings.shader_type]}
    for role_id, suffixes in ROLE_SUFFIX_CANDIDATES.items():
        if role_id not in required_roles:
            continue
        if getattr(settings, role_id):
            continue

        guessed = ""
        for suffix in suffixes:
            guessed = _derive_texture_path(settings.tex_d, suffix)
            if guessed:
                break
        if not guessed:
            guessed = _guess_texture_by_scan(settings.tex_d, role_id)
        if guessed:
            setattr(settings, role_id, guessed)
            filled += 1
    return filled


def _sanitize_name(value: str) -> str:
    value = re.sub(r"[^0-9A-Za-z_\u4e00-\u9fff]+", "_", value).strip("_")
    return value or "Target"


def _find_armature(obj):
    armature = obj.find_armature()
    if armature:
        return armature
    for modifier in obj.modifiers:
        if modifier.type == "ARMATURE" and modifier.object:
            return modifier.object
    return None


def _find_bone_case_insensitive(armature_obj, bone_name: str):
    if not armature_obj or armature_obj.type != "ARMATURE" or not bone_name:
        return None
    bone = armature_obj.data.bones.get(bone_name)
    if bone is not None:
        return bone
    lowered = bone_name.casefold()
    for candidate in armature_obj.data.bones:
        if candidate.name.casefold() == lowered:
            return candidate
    return None


def _find_head_bone(armature_obj, preferred_name: str = ""):
    if not armature_obj or armature_obj.type != "ARMATURE":
        return None

    preferred = _find_bone_case_insensitive(armature_obj, preferred_name)
    if preferred is not None:
        return preferred

    bones = list(armature_obj.data.bones)
    if not bones:
        return None

    exact_lookup = {name.casefold() for name in HEAD_BONE_EXACT_NAMES}
    for bone in bones:
        if bone.name.casefold() in exact_lookup:
            return bone

    def score_bone_name(name: str) -> int:
        lowered = name.casefold()
        if any(excluded in lowered for excluded in HEAD_BONE_EXCLUDE_KEYWORDS):
            return -1
        score = 0
        for keyword in HEAD_BONE_KEYWORDS:
            keyword_lower = keyword.casefold()
            if lowered == keyword_lower:
                score = max(score, 200)
            elif lowered.endswith(keyword_lower):
                score = max(score, 120)
            elif keyword_lower in lowered:
                score = max(score, 80)
        if lowered.startswith("def-") or lowered.startswith("def_"):
            score -= 10
        return score

    ranked = sorted(
        ((score_bone_name(bone.name), bone.name.casefold(), bone) for bone in bones),
        key=lambda item: (-item[0], item[1]),
    )
    return ranked[0][2] if ranked and ranked[0][0] > 0 else None


def _resolve_helper_armature(settings: ENDFIELD_PG_Settings, obj):
    if getattr(settings, "head_bone_armature", None) and settings.head_bone_armature.type == "ARMATURE":
        return settings.head_bone_armature
    return _find_armature(obj)


def _resolve_head_bone(settings: ENDFIELD_PG_Settings, obj):
    armature = _resolve_helper_armature(settings, obj)
    if armature is None:
        return None, None
    bone = _find_head_bone(armature, getattr(settings, "head_bone_name", ""))
    return armature, bone


def _resolve_lattice_bone(armature_obj, head_bone):
    if armature_obj is None or head_bone is None:
        return None
    preferred_names = []
    if head_bone.name:
        if head_bone.name.startswith(LATTICE_BONE_PREFIXES):
            preferred_names.append(head_bone.name)
        else:
            preferred_names.extend(f"{prefix}{head_bone.name}" for prefix in LATTICE_BONE_PREFIXES)
    preferred_names.extend(["DEF-Head", "DEF_head", "def-head", "def_head"])
    for name in preferred_names:
        bone = _find_bone_case_insensitive(armature_obj, name)
        if bone is not None:
            return bone
    return head_bone


def _estimate_anchor_from_bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    center = sum(points, Vector()) / len(points)
    max_z = max(point.z for point in points)
    return Vector((center.x, center.y, max_z - max(obj.dimensions) * 0.15))


def _bounds_world_min_max(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    min_corner = Vector((min(point.x for point in points), min(point.y for point in points), min(point.z for point in points)))
    max_corner = Vector((max(point.x for point in points), max(point.y for point in points), max(point.z for point in points)))
    return min_corner, max_corner


def _fit_lattice_to_object(lattice_obj, obj):
    if lattice_obj is None or obj is None:
        return
    if lattice_obj.type == "LATTICE":
        data = lattice_obj.data
        if data is not None:
            for attr_name in ("interpolation_type_u", "interpolation_type_v", "interpolation_type_w"):
                if hasattr(data, attr_name):
                    setattr(data, attr_name, "KEY_BSPLINE")
            if hasattr(data, "use_outside"):
                data.use_outside = False
    lattice_obj.delta_location = (0.0, 0.0, 0.0)
    lattice_obj.delta_rotation_euler = (0.0, 0.0, 0.0)
    lattice_obj.delta_scale = (1.0, 1.0, 1.0)
    min_corner, max_corner = _bounds_world_min_max(obj)
    center = (min_corner + max_corner) * 0.5
    size = (max_corner - min_corner)
    lattice_obj.rotation_euler = (0.0, 0.0, 0.0)
    lattice_obj.location = center
    lattice_obj.scale = (
        max(size.x * 0.5 * LATTICE_FIT_MARGIN.x, 0.001),
        max(size.y * 0.5 * LATTICE_FIT_MARGIN.y, 0.001),
        max(size.z * 0.5 * LATTICE_FIT_MARGIN.z, 0.001),
    )


def _validate_face_helper_targets(settings: ENDFIELD_PG_Settings, objects):
    if settings.shader_type != "FACE":
        return ""
    for obj in objects:
        armature, head_bone = _resolve_head_bone(settings, obj)
        if armature is None:
            return f"对象 {obj.name} 未找到骨架，请先指定头部骨骼用的骨架"
        if head_bone is None:
            return f"对象 {obj.name} 未找到头部骨骼，请在脸部栏指定头部骨骼"
    return ""


def _find_collection_child(parent, name: str):
    for child in parent.children:
        if child.name == name:
            return child
    return None


def _unlink_collection_from_parents(collection, keep_parent=None):
    if collection is None:
        return
    all_parents = [bpy.context.scene.collection, *bpy.data.collections]
    for parent in all_parents:
        if parent == keep_parent:
            continue
        child = _find_collection_child(parent, collection.name)
        if child == collection:
            try:
                parent.children.unlink(collection)
            except RuntimeError:
                pass


def _ensure_collection_child(parent, name: str):
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
    _unlink_collection_from_parents(collection, keep_parent=parent)
    if _find_collection_child(parent, name) is None:
        parent.children.link(collection)
    return collection


def _find_layer_collection(layer_collection, collection_name: str):
    if layer_collection is None:
        return None
    if layer_collection.collection and layer_collection.collection.name == collection_name:
        return layer_collection
    for child in layer_collection.children:
        found = _find_layer_collection(child, collection_name)
        if found is not None:
            return found
    return None


def _set_collection_excluded(scene, collection_name: str, excluded=True):
    if scene is None or not collection_name:
        return
    for view_layer in scene.view_layers:
        layer_collection = _find_layer_collection(view_layer.layer_collection, collection_name)
        if layer_collection is not None:
            layer_collection.exclude = excluded


def _remove_collection_if_empty(name: str):
    collection = bpy.data.collections.get(name)
    if collection is None:
        return
    if collection.objects or collection.children:
        return
    _unlink_collection_from_parents(collection)
    try:
        bpy.data.collections.remove(collection)
    except RuntimeError:
        pass


def _ensure_master_structure():
    _normalize_legacy_scene_names()
    scene = bpy.context.scene
    scene_root = scene.collection
    master = _ensure_collection_child(scene_root, MASTER_COLLECTION_NAME)
    helper = bpy.data.collections.get(HELPER_COLLECTION_NAME)
    if helper is None:
        helper = bpy.data.collections.new(HELPER_COLLECTION_NAME)
    _unlink_collection_from_parents(helper, keep_parent=master)
    if _find_collection_child(master, helper.name) is None:
        master.children.link(helper)
    _ensure_collection_child(helper, UTILITY_COLLECTION_NAME)
    _ensure_collection_child(helper, WIDGETS_COLLECTION_NAME)
    _ensure_collection_child(helper, META_COLLECTION_NAME)
    _remove_collection_if_empty(MESH_HIGH_COLLECTION_NAME)
    _remove_collection_if_empty(MESH_LOW_COLLECTION_NAME)
    _remove_collection_if_empty(MESH_COLLECTION_NAME)
    _remove_collection_if_empty(RIG_COLLECTION_NAME)
    _set_collection_excluded(scene, MASTER_COLLECTION_NAME, True)
    return {
        "master": master,
        "helper": helper,
    }


def _link_object_to_collection(obj, collection):
    if collection and obj is not None:
        names = {item.name for item in collection.objects}
        if obj.name not in names:
            try:
                collection.objects.link(obj)
            except RuntimeError:
                pass


def _move_object_to_collection(obj, target_collection, exclusive=False):
    if obj is None or target_collection is None:
        return
    if exclusive:
        for collection in list(obj.users_collection):
            if collection != target_collection:
                try:
                    collection.objects.unlink(obj)
                except RuntimeError:
                    pass
    _link_object_to_collection(obj, target_collection)


def _get_or_create_empty(name: str, collection):
    obj = bpy.data.objects.get(name)
    if obj is None:
        obj = bpy.data.objects.new(name, None)
        obj.empty_display_type = "PLAIN_AXES"
        obj.empty_display_size = 1.0
    _link_object_to_collection(obj, collection)
    return obj


def _ensure_scene_camera(settings: ENDFIELD_PG_Settings, target_collection=None):
    scene = bpy.context.scene
    scene_root = scene.collection
    library = _effective_library_path(settings)
    camera_obj = _find_or_append_object(library, SOURCE_CAMERA_NAME) if library else bpy.data.objects.get(SOURCE_CAMERA_NAME)
    if camera_obj is None or camera_obj.type != "CAMERA":
        camera_obj = scene.camera if scene.camera and scene.camera.type == "CAMERA" else None
    if camera_obj is None:
        return None
    target_collection = target_collection or scene_root
    is_source_camera = _name_matches_datablock(SOURCE_CAMERA_NAME, camera_obj.name)
    _move_object_to_collection(camera_obj, target_collection, exclusive=is_source_camera)
    scene.camera = camera_obj
    return camera_obj


def _clear_parent_keep_transform(obj):
    matrix_world = obj.matrix_world.copy()
    obj.parent = None
    obj.parent_type = "OBJECT"
    obj.parent_bone = ""
    obj.matrix_world = matrix_world


def _target_matrix(target, subtarget=""):
    if target is None:
        return Matrix.Identity(4)
    if subtarget and target.type == "ARMATURE" and target.pose and target.pose.bones.get(subtarget):
        return target.matrix_world @ target.pose.bones[subtarget].matrix
    return target.matrix_world.copy()


def _ensure_child_of_constraint(obj, name: str, target=None, subtarget: str = ""):
    constraint = None
    for item in obj.constraints:
        if item.type == "CHILD_OF" and item.name == name:
            constraint = item
            break
    if constraint is None:
        constraint = obj.constraints.new("CHILD_OF")
        constraint.name = name
    _clear_parent_keep_transform(obj)
    constraint.target = target
    constraint.subtarget = subtarget
    bpy.context.view_layer.update()
    if hasattr(constraint, "set_inverse_pending"):
        constraint.set_inverse_pending = True
    bpy.context.view_layer.update()
    return constraint


def _ensure_track_to_constraint(obj, name: str, target=None):
    if obj is None:
        return None
    constraint = None
    for item in obj.constraints:
        if item.type == "TRACK_TO" and item.name == name:
            constraint = item
            break
    if constraint is None:
        constraint = obj.constraints.new("TRACK_TO")
        constraint.name = name
    constraint.target = target
    constraint.track_axis = "TRACK_Y"
    constraint.up_axis = "UP_X"
    constraint.target_space = "WORLD"
    constraint.owner_space = "WORLD"
    if hasattr(constraint, "use_target_z"):
        constraint.use_target_z = False
    return constraint


def _remove_child_of_constraints(obj):
    if obj is None:
        return
    for item in list(obj.constraints):
        if item.type == "CHILD_OF":
            obj.constraints.remove(item)


def _remove_track_to_constraints(obj):
    if obj is None:
        return
    for item in list(obj.constraints):
        if item.type == "TRACK_TO":
            obj.constraints.remove(item)


def _replace_child_of_constraint(obj, name: str, target=None, subtarget: str = "", desired_world=None):
    if obj is None:
        return None
    desired_world = desired_world.copy() if desired_world is not None else obj.matrix_world.copy()
    _remove_child_of_constraints(obj)
    bpy.context.view_layer.update()
    obj.matrix_world = desired_world
    return _ensure_child_of_constraint(obj, name, target, subtarget)


def _set_object_info_target(node, target_obj) -> bool:
    if node is None or target_obj is None:
        return False
    socket = node.inputs.get("Object") if hasattr(node, "inputs") else None
    if socket is None:
        return False
    try:
        socket.default_value = target_obj
        return True
    except Exception:
        return False


def _rebind_sun_vec_targets(node_group, lf, lc):
    if node_group is None:
        return False

    object_nodes = [
        node for node in node_group.nodes
        if getattr(node, "type", "") == "OBJECT_INFO" or getattr(node, "bl_idname", "") == "GeometryNodeObjectInfo"
    ]
    if not object_nodes:
        return False

    rebound = False
    unresolved = []
    for node in object_nodes:
        socket = node.inputs.get("Object") if hasattr(node, "inputs") else None
        current_obj = getattr(socket, "default_value", None) if socket else None
        node_hint = f"{node.name} {node.label}".lower()
        current_name = current_obj.name.lower() if current_obj else ""

        if "lf" in node_hint or current_name == SUN_HELPER_LF_NAME.lower():
            rebound = _set_object_info_target(node, lf) or rebound
            continue
        if "lc" in node_hint or current_name == SUN_HELPER_LC_NAME.lower():
            rebound = _set_object_info_target(node, lc) or rebound
            continue

        unresolved.append(node)

    fallback_targets = [lf, lc]
    for node, target in zip(unresolved, fallback_targets):
        rebound = _set_object_info_target(node, target) or rebound

    return rebound


def _sync_material_alpha_settings(material, template):
    if material is None or template is None:
        return

    for attr_name in ("shadow_method", "use_backface_culling"):
        if hasattr(material, attr_name) and hasattr(template, attr_name):
            try:
                setattr(material, attr_name, getattr(template, attr_name))
            except Exception:
                pass

    if hasattr(material, "surface_render_method") and hasattr(template, "surface_render_method"):
        try:
            material.surface_render_method = template.surface_render_method
        except Exception:
            pass

    if hasattr(material, "blend_method") and hasattr(template, "blend_method"):
        try:
            material.blend_method = template.blend_method
        except Exception:
            pass


def _migrate_scene_environment(settings: ENDFIELD_PG_Settings, target_scene):
    if not settings.migrate_source_environment:
        return
    world = _ensure_target_world(settings)
    if world is not None:
        target_scene.world = world
        _cleanup_unused_world_backups()


def _ensure_sun_rig(settings: ENDFIELD_PG_Settings):
    library = _effective_library_path(settings)
    structure = _ensure_master_structure()
    helper_collection = _find_or_append_collection(library, HELPER_COLLECTION_NAME) if library else None
    if helper_collection is not None:
        _unlink_collection_from_parents(helper_collection, keep_parent=structure["master"])
        if _find_collection_child(structure["master"], helper_collection.name) is None:
            structure["master"].children.link(helper_collection)
        structure["helper"] = helper_collection
        _ensure_collection_child(helper_collection, UTILITY_COLLECTION_NAME)
        _ensure_collection_child(helper_collection, WIDGETS_COLLECTION_NAME)
        _ensure_collection_child(helper_collection, META_COLLECTION_NAME)
    elif library:
        for child_name in (UTILITY_COLLECTION_NAME, WIDGETS_COLLECTION_NAME, META_COLLECTION_NAME):
            child_collection = _find_or_append_collection(library, child_name)
            if child_collection is not None:
                _unlink_collection_from_parents(child_collection, keep_parent=structure["helper"])
                if _find_collection_child(structure["helper"], child_collection.name) is None:
                    structure["helper"].children.link(child_collection)

    helper_collection = structure["helper"]
    utility_collection = _find_collection_child(helper_collection, UTILITY_COLLECTION_NAME)
    if library and utility_collection is not None:
        for object_name in ("Active Camera Tracker", "Lattice", "Pencil+ 4 Line Merge Helper"):
            utility_obj = _find_or_append_object(library, object_name)
            if utility_obj is not None:
                _move_object_to_collection(utility_obj, utility_collection)

    light_obj = _find_or_append_object(library, SUN_LIGHT_NAME) if library else bpy.data.objects.get(SUN_LIGHT_NAME)
    if light_obj is None or light_obj.type != "LIGHT":
        light_data = bpy.data.lights.get(SUN_LIGHT_NAME)
        if light_data is None:
            light_data = bpy.data.lights.new(SUN_LIGHT_NAME, "SUN")
        else:
            light_data.type = "SUN"
        light_obj = bpy.data.objects.get(SUN_LIGHT_NAME) or bpy.data.objects.new(SUN_LIGHT_NAME, light_data)
    _move_object_to_collection(light_obj, bpy.context.scene.collection, exclusive=True)
    light_obj.location = SUN_LIGHT_LOCATION
    light_obj.rotation_euler = SUN_LIGHT_ROTATION
    light_obj.data.type = "SUN"
    light_obj.data.energy = 1.0
    if hasattr(light_obj.data, "angle"):
        light_obj.data.angle = 0.009180432185530663
    camera_obj = _ensure_scene_camera(settings, bpy.context.scene.collection)

    lc = _find_or_append_object(library, SUN_HELPER_LC_NAME) if library else bpy.data.objects.get(SUN_HELPER_LC_NAME)
    lf = _find_or_append_object(library, SUN_HELPER_LF_NAME) if library else bpy.data.objects.get(SUN_HELPER_LF_NAME)
    lc = lc or _get_or_create_empty(SUN_HELPER_LC_NAME, helper_collection)
    lf = lf or _get_or_create_empty(SUN_HELPER_LF_NAME, helper_collection)
    _move_object_to_collection(lc, helper_collection)
    _move_object_to_collection(lf, helper_collection)
    _remove_child_of_constraints(lc)
    _remove_child_of_constraints(lf)
    bpy.context.view_layer.update()
    lc.location = light_obj.matrix_world @ Vector((0.0, 0.0, -SUN_LC_DISTANCE))
    lf.location = light_obj.matrix_world @ Vector((0.0, 0.0, -SUN_LF_DISTANCE))
    lc.rotation_euler = (0.0, 0.0, 0.0)
    lf.rotation_euler = (0.0, 0.0, 0.0)
    lc.scale = (0.240563393, 0.240563393, 0.240563393)
    lf.scale = (0.240563393, 0.240563393, 0.240563393)
    bpy.context.view_layer.update()
    lc_world = lc.matrix_world.copy()
    lf_world = lf.matrix_world.copy()
    _ensure_child_of_constraint(lc, "瀛愮骇", light_obj)
    _ensure_child_of_constraint(lf, "瀛愮骇", light_obj)

    _replace_child_of_constraint(lc, "子级", light_obj)
    _replace_child_of_constraint(lf, "子级", light_obj)

    _replace_child_of_constraint(lc, "Child Of", light_obj, desired_world=lc_world)
    _replace_child_of_constraint(lf, "Child Of", light_obj, desired_world=lf_world)

    sun_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["SUN_VEC"])
    _rebind_sun_vec_targets(sun_group, lf, lc)
    return {"sun": light_obj, "camera": camera_obj, "helper_collection": helper_collection, "lc": lc, "lf": lf}


def _ensure_head_helper_rig(settings: ENDFIELD_PG_Settings, obj):
    sun_rig = _ensure_sun_rig(settings)
    helper_collection = sun_rig["helper_collection"]
    armature, head_bone = _resolve_head_bone(settings, obj)
    if armature is None or head_bone is None:
        return None
    lattice_bone = _resolve_lattice_bone(armature, head_bone)
    anchor = armature.matrix_world @ head_bone.head_local

    library = _effective_library_path(settings)
    hc = _find_or_append_object(library, HEAD_HELPER_NAME) if library else bpy.data.objects.get(HEAD_HELPER_NAME)
    hf = _find_or_append_object(library, HEAD_FORWARD_NAME) if library else bpy.data.objects.get(HEAD_FORWARD_NAME)
    hr = _find_or_append_object(library, HEAD_RIGHT_NAME) if library else bpy.data.objects.get(HEAD_RIGHT_NAME)
    hc = hc or _get_or_create_empty(HEAD_HELPER_NAME, helper_collection)
    hf = hf or _get_or_create_empty(HEAD_FORWARD_NAME, helper_collection)
    hr = hr or _get_or_create_empty(HEAD_RIGHT_NAME, helper_collection)
    _move_object_to_collection(hc, helper_collection)
    _move_object_to_collection(hf, helper_collection)
    _move_object_to_collection(hr, helper_collection)
    _remove_child_of_constraints(hc)
    bpy.context.view_layer.update()

    hc.scale = HEAD_HELPER_SCALE
    hf.scale = HEAD_DIRECTION_SCALE
    hr.scale = HEAD_DIRECTION_SCALE
    hc.location = anchor
    bpy.context.view_layer.update()
    hc_world = hc.matrix_world.copy()
    _replace_child_of_constraint(hc, "Child Of", armature, head_bone.name, desired_world=hc_world)

    _clear_parent_keep_transform(hf)
    _clear_parent_keep_transform(hr)
    hf.parent = hc
    hr.parent = hc
    hf.matrix_parent_inverse = hc.matrix_world.inverted_safe()
    hr.matrix_parent_inverse = hc.matrix_world.inverted_safe()
    hf.location = anchor + HEAD_FORWARD_OFFSET
    hr.location = anchor + HEAD_RIGHT_OFFSET
    hf.rotation_euler = (0.0, 0.0, 0.0)
    hr.rotation_euler = (0.0, 0.0, 0.0)

    lattice = _find_matching_object(LATTICE_OBJECT_BASENAME)
    if lattice is None and library:
        lattice = _find_or_append_object(library, LATTICE_OBJECT_BASENAME)
    utility_collection = _find_collection_child(helper_collection, UTILITY_COLLECTION_NAME)
    if lattice is not None and utility_collection is not None:
        _move_object_to_collection(lattice, utility_collection)
        _remove_child_of_constraints(lattice)
        bpy.context.view_layer.update()
        _fit_lattice_to_object(lattice, obj)
        bpy.context.view_layer.update()
        lattice_world = lattice.matrix_world.copy()
        _replace_child_of_constraint(
            lattice,
            "Child Of",
            armature,
            lattice_bone.name if lattice_bone else head_bone.name,
            desired_world=lattice_world,
        )
        tracker = _find_matching_object("Active Camera Tracker")
        if tracker is not None:
            _ensure_track_to_constraint(lattice, "Track To", tracker)

    return {"HC": hc, "HF": hf, "HR": hr, "SUN": sun_rig["sun"]}


def _ensure_sun_rig(settings: ENDFIELD_PG_Settings):
    library = _effective_library_path(settings)
    structure = _ensure_master_structure()
    helper_collection = _find_or_append_collection(library, HELPER_COLLECTION_NAME) if library else None
    if helper_collection is not None:
        _normalize_helper_collection_tree(helper_collection)
        _unlink_collection_from_parents(helper_collection, keep_parent=structure["master"])
        if _find_collection_child(structure["master"], helper_collection.name) is None:
            structure["master"].children.link(helper_collection)
        structure["helper"] = helper_collection
        _ensure_collection_child(helper_collection, UTILITY_COLLECTION_NAME)
        _ensure_collection_child(helper_collection, WIDGETS_COLLECTION_NAME)
        _ensure_collection_child(helper_collection, META_COLLECTION_NAME)
    elif library:
        for source_name, child_name in (
            (SOURCE_UTILITY_COLLECTION_NAME, UTILITY_COLLECTION_NAME),
            (SOURCE_WIDGETS_COLLECTION_NAME, WIDGETS_COLLECTION_NAME),
            (SOURCE_META_COLLECTION_NAME, META_COLLECTION_NAME),
        ):
            child_collection = _find_or_append_collection(library, source_name)
            if child_collection is not None:
                child_collection = _rename_datablock(bpy.data.collections, child_collection, child_name)
                _unlink_collection_from_parents(child_collection, keep_parent=structure["helper"])
                if _find_collection_child(structure["helper"], child_collection.name) is None:
                    structure["helper"].children.link(child_collection)

    helper_collection = structure["helper"]
    utility_collection = _find_collection_child(helper_collection, UTILITY_COLLECTION_NAME)
    if library and utility_collection is not None:
        for object_name in ("Active Camera Tracker", "Lattice", "Pencil+ 4 Line Merge Helper"):
            utility_obj = _find_or_append_object(library, object_name)
            if utility_obj is not None:
                _move_object_to_collection(utility_obj, utility_collection)

    light_obj = _find_or_append_object(library, SOURCE_SUN_LIGHT_NAME) if library else _ensure_object_alias(SUN_LIGHT_NAME, SOURCE_SUN_LIGHT_NAME)
    if light_obj is None or light_obj.type != "LIGHT":
        light_data = bpy.data.lights.get(SUN_LIGHT_NAME)
        if light_data is None:
            light_data = bpy.data.lights.new(SUN_LIGHT_NAME, "SUN")
        else:
            light_data.type = "SUN"
        light_obj = bpy.data.objects.get(SUN_LIGHT_NAME) or bpy.data.objects.new(SUN_LIGHT_NAME, light_data)
    light_obj = _rename_datablock(bpy.data.objects, light_obj, SUN_LIGHT_NAME)
    _move_object_to_collection(light_obj, bpy.context.scene.collection, exclusive=True)
    light_obj.location = SUN_LIGHT_LOCATION
    light_obj.rotation_euler = SUN_LIGHT_ROTATION
    light_obj.data.type = "SUN"
    light_obj.data.energy = 1.0
    if hasattr(light_obj.data, "angle"):
        light_obj.data.angle = 0.009180432185530663
    camera_obj = _ensure_scene_camera(settings, bpy.context.scene.collection)

    lc = _find_or_append_object(library, SUN_HELPER_LC_NAME) if library else _find_matching_object(SUN_HELPER_LC_NAME)
    lf = _find_or_append_object(library, SUN_HELPER_LF_NAME) if library else _find_matching_object(SUN_HELPER_LF_NAME)
    lc = lc or _get_or_create_empty(SUN_HELPER_LC_NAME, helper_collection)
    lf = lf or _get_or_create_empty(SUN_HELPER_LF_NAME, helper_collection)
    _move_object_to_collection(lc, helper_collection)
    _move_object_to_collection(lf, helper_collection)
    _remove_child_of_constraints(lc)
    _remove_child_of_constraints(lf)
    bpy.context.view_layer.update()

    lc.location = light_obj.matrix_world @ Vector((0.0, 0.0, -SUN_LC_DISTANCE))
    lf.location = light_obj.matrix_world @ Vector((0.0, 0.0, -SUN_LF_DISTANCE))
    lc.rotation_euler = (0.0, 0.0, 0.0)
    lf.rotation_euler = (0.0, 0.0, 0.0)
    lc.scale = (0.240563393, 0.240563393, 0.240563393)
    lf.scale = (0.240563393, 0.240563393, 0.240563393)
    bpy.context.view_layer.update()
    lc_world = lc.matrix_world.copy()
    lf_world = lf.matrix_world.copy()
    _replace_child_of_constraint(lc, "Child Of", light_obj, desired_world=lc_world)
    _replace_child_of_constraint(lf, "Child Of", light_obj, desired_world=lf_world)

    sun_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["SUN_VEC"])
    _rebind_sun_vec_targets(sun_group, lf, lc)
    return {"sun": light_obj, "camera": camera_obj, "helper_collection": helper_collection, "lc": lc, "lf": lf}


def _ensure_head_helper_rig(settings: ENDFIELD_PG_Settings, obj):
    sun_rig = _ensure_sun_rig(settings)
    helper_collection = sun_rig["helper_collection"]
    armature, head_bone = _resolve_head_bone(settings, obj)
    if armature is None or head_bone is None:
        return None
    lattice_bone = _resolve_lattice_bone(armature, head_bone)
    anchor = armature.matrix_world @ head_bone.head_local

    library = _effective_library_path(settings)
    hc = _find_or_append_object(library, SOURCE_HEAD_HELPER_NAME) if library else _ensure_object_alias(HEAD_HELPER_NAME, SOURCE_HEAD_HELPER_NAME)
    hf = _find_or_append_object(library, SOURCE_HEAD_FORWARD_NAME) if library else _ensure_object_alias(HEAD_FORWARD_NAME, SOURCE_HEAD_FORWARD_NAME)
    hr = _find_or_append_object(library, SOURCE_HEAD_RIGHT_NAME) if library else _ensure_object_alias(HEAD_RIGHT_NAME, SOURCE_HEAD_RIGHT_NAME)
    hc = _rename_datablock(bpy.data.objects, hc, HEAD_HELPER_NAME) if hc is not None else None
    hf = _rename_datablock(bpy.data.objects, hf, HEAD_FORWARD_NAME) if hf is not None else None
    hr = _rename_datablock(bpy.data.objects, hr, HEAD_RIGHT_NAME) if hr is not None else None
    hc = hc or _get_or_create_empty(HEAD_HELPER_NAME, helper_collection)
    hf = hf or _get_or_create_empty(HEAD_FORWARD_NAME, helper_collection)
    hr = hr or _get_or_create_empty(HEAD_RIGHT_NAME, helper_collection)
    _move_object_to_collection(hc, helper_collection)
    _move_object_to_collection(hf, helper_collection)
    _move_object_to_collection(hr, helper_collection)

    _remove_child_of_constraints(hc)
    bpy.context.view_layer.update()
    hc.scale = HEAD_HELPER_SCALE
    hc.location = anchor
    hc.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    hc_world = hc.matrix_world.copy()
    _replace_child_of_constraint(hc, "Child Of", armature, head_bone.name, desired_world=hc_world)

    _clear_parent_keep_transform(hf)
    _clear_parent_keep_transform(hr)
    hf.parent = hc
    hr.parent = hc
    hf.matrix_parent_inverse = hc.matrix_world.inverted_safe()
    hr.matrix_parent_inverse = hc.matrix_world.inverted_safe()
    hf.scale = HEAD_DIRECTION_SCALE
    hr.scale = HEAD_DIRECTION_SCALE
    hf.location = anchor + HEAD_FORWARD_OFFSET
    hr.location = anchor + HEAD_RIGHT_OFFSET
    hf.rotation_euler = (0.0, 0.0, 0.0)
    hr.rotation_euler = (0.0, 0.0, 0.0)

    lattice = _find_or_append_object(library, LATTICE_OBJECT_BASENAME) if library else _find_matching_object(LATTICE_OBJECT_BASENAME)
    utility_collection = _find_collection_child(helper_collection, UTILITY_COLLECTION_NAME)
    if lattice is not None and utility_collection is not None:
        _move_object_to_collection(lattice, utility_collection)
        _remove_child_of_constraints(lattice)
        _remove_track_to_constraints(lattice)
        bpy.context.view_layer.update()
        _fit_lattice_to_object(lattice, obj)
        bpy.context.view_layer.update()
        lattice_world = lattice.matrix_world.copy()
        _replace_child_of_constraint(
            lattice,
            "Child Of",
            armature,
            lattice_bone.name if lattice_bone else head_bone.name,
            desired_world=lattice_world,
        )
        tracker = _find_or_append_object(library, "Active Camera Tracker") if library else _find_matching_object("Active Camera Tracker")
        if tracker is not None:
            _ensure_track_to_constraint(lattice, "Track To", tracker)

    return {"HC": hc, "HF": hf, "HR": hr, "SUN": sun_rig["sun"]}


def _current_head_helper_rig():
    hc = _ensure_object_alias(HEAD_HELPER_NAME, SOURCE_HEAD_HELPER_NAME)
    hf = _ensure_object_alias(HEAD_FORWARD_NAME, SOURCE_HEAD_FORWARD_NAME)
    hr = _ensure_object_alias(HEAD_RIGHT_NAME, SOURCE_HEAD_RIGHT_NAME)
    sun = _ensure_object_alias(SUN_LIGHT_NAME, SOURCE_SUN_LIGHT_NAME)
    if hc is None or hf is None or hr is None or sun is None:
        return None
    return {"HC": hc, "HF": hf, "HR": hr, "SUN": sun}


def _find_material_slot(obj, keywords):
    for slot in obj.material_slots:
        material = slot.material
        if not material:
            continue
        name = material.name.lower()
        if any(keyword in name for keyword in keywords):
            return material
    return None


def _ensure_eye_support_materials(settings: ENDFIELD_PG_Settings, obj):
    library = _effective_library_path(settings)
    support = {
        "iris": _find_or_append_first_material(library, TEMPLATE_MATERIAL_PREFS["PUPIL"]),
        "brow": _find_or_append_first_material(library, TEMPLATE_MATERIAL_PREFS["BROW"]),
        "iris_alpha": _find_or_append_first_material(library, ALPHA_TEMPLATE_PREFS["IRIS"]),
        "brow_alpha": _find_or_append_first_material(library, ALPHA_TEMPLATE_PREFS["BROW"]),
    }

    brow_keywords = ("brow", "lash", "eyelash")
    for slot in obj.material_slots:
        material = slot.material
        if not material:
            continue
        name = material.name.lower()
        if support["brow"] and any(keyword in name for keyword in brow_keywords):
            slot.material = support["brow"]

    return support


def _iter_related_mesh_objects(obj):
    armature = _find_armature(obj)
    parent = obj.parent
    collections = set(obj.users_collection)
    related = []
    for candidate in bpy.data.objects:
        if candidate == obj or candidate.type != "MESH":
            continue
        if armature and _find_armature(candidate) == armature:
            related.append(candidate)
            continue
        if parent and candidate.parent == parent:
            related.append(candidate)
            continue
        if collections.intersection(candidate.users_collection):
            related.append(candidate)
    return related


def _remove_modifier_by_name(obj, modifier_name: str):
    modifier = obj.modifiers.get(modifier_name)
    if modifier is not None:
        obj.modifiers.remove(modifier)


def _remove_eye_transparency_modifiers(obj):
    for modifier in list(obj.modifiers):
        if modifier.type != "NODES":
            continue
        node_group_name = modifier.node_group.name if modifier.node_group else ""
        if modifier.name.startswith(EYE_TRANSPARENCY_MODIFIER_PREFIX) or node_group_name in GEOMETRY_NODE_PREFS["EYE_TRANSPARENCY"]:
            obj.modifiers.remove(modifier)


def _attach_named_geo_modifier(obj, node_group, name: str):
    modifier = obj.modifiers.get(name)
    if modifier is None or modifier.type != "NODES":
        modifier = obj.modifiers.new(name, "NODES")
    modifier.name = name
    modifier.node_group = node_group
    return modifier


def _remove_face_outline_modifiers(obj):
    for modifier in list(obj.modifiers):
        if modifier.type == "SOLIDIFY":
            obj.modifiers.remove(modifier)


def _remove_solidify_outline_modifiers(obj):
    for modifier in list(obj.modifiers):
        if modifier.type == "SOLIDIFY":
            obj.modifiers.remove(modifier)


def _ensure_modifier_sequence(obj, modifiers, after_types=("ARMATURE",)):
    target_index = 0
    for index, modifier in enumerate(obj.modifiers):
        if modifier.type in after_types:
            target_index = index + 1
    for modifier in modifiers:
        if modifier is None:
            continue
        current_index = obj.modifiers.find(modifier.name)
        if current_index < 0:
            continue
        if current_index != target_index:
            obj.modifiers.move(current_index, target_index)
        target_index += 1


def _copy_alpha_template(settings: ENDFIELD_PG_Settings, role: str, base_material, target_name: str):
    library = _effective_library_path(settings)
    template = _find_or_append_first_material(library, ALPHA_TEMPLATE_PREFS[role])
    if template is None:
        template = bpy.data.materials.get(target_name)
    if template is None:
        template = _create_fallback_alpha_material(target_name)
        template.name = target_name
        return template

    material = bpy.data.materials.get(target_name)
    if material is None:
        material = template.copy()
        material.name = target_name

    base_nodes = _find_nodes_for_role(base_material, "tex_d")
    source_image = base_nodes[0].image if base_nodes else None
    if source_image is None:
        for node in _iter_tex_image_nodes(base_material):
            image = getattr(node, "image", None)
            if _image_is_usable(image):
                source_image = image
                break
    if source_image is not None:
        for node in _iter_tex_image_nodes(material):
            node.image = source_image
    _sync_material_alpha_settings(material, template)
    return material


def _ensure_face_material_bundle(settings: ENDFIELD_PG_Settings, obj, face_material=None, related_objects=None, support_materials=None):
    support_materials = support_materials or {}
    iris_material = _find_material_slot(obj, ("iris", "eye", "pupil"))
    brow_material = _find_material_slot(obj, ("brow", "lash", "eyelash"))
    if iris_material is None:
        iris_material = _find_material_slot(obj, ("iris", "eye", "pupil"))
    if brow_material is None:
        brow_material = _find_material_slot(obj, ("brow", "lash", "eyelash"))
    for related in related_objects or ():
        if iris_material is None:
            iris_material = _find_material_slot(related, ("iris", "eye", "eyel", "pupil"))
        if brow_material is None:
            brow_material = _find_material_slot(related, ("brow", "lash", "eyelash"))
        if iris_material is not None and brow_material is not None:
            break
    iris_material = iris_material or support_materials.get("iris")
    brow_material = brow_material or support_materials.get("brow")
    iris_alpha = _copy_alpha_template(settings, "IRIS", iris_material, f"{iris_material.name}_AlphaProxy") if iris_material else support_materials.get("iris_alpha")
    brow_alpha = _copy_alpha_template(settings, "BROW", brow_material, f"{brow_material.name}_AlphaProxy") if brow_material else support_materials.get("brow_alpha")
    return {
        "face": face_material,
        "iris": iris_material,
        "brow": brow_material,
        "iris_alpha": iris_alpha,
        "brow_alpha": brow_alpha,
    }


def _find_material_by_shader_type(obj, shader_type: str):
    if obj is None:
        return None
    for slot in obj.material_slots:
        material = slot.material
        if material is None:
            continue
        if _detect_shader_type_from_material(material) == shader_type:
            return material
    return None


def _ensure_eye_support_materials(settings: ENDFIELD_PG_Settings, obj):
    library = _effective_library_path(settings)
    return {
        "iris": _find_or_append_first_material(library, TEMPLATE_MATERIAL_PREFS["PUPIL"]),
        "brow": _find_or_append_first_material(library, TEMPLATE_MATERIAL_PREFS["BROW"]),
        "iris_alpha": _find_or_append_first_material(library, ALPHA_TEMPLATE_PREFS["IRIS"]),
        "brow_alpha": _find_or_append_first_material(library, ALPHA_TEMPLATE_PREFS["BROW"]),
    }


def _ensure_face_material_bundle(settings: ENDFIELD_PG_Settings, obj, face_material=None, related_objects=None, support_materials=None):
    support_materials = support_materials or {}
    related_objects = list(related_objects or ())

    iris_material = face_material if _detect_shader_type_from_material(face_material) == "PUPIL" else None
    brow_material = face_material if _detect_shader_type_from_material(face_material) == "BROW" else None

    for candidate_obj in (obj, *related_objects):
        if iris_material is None:
            iris_material = _find_material_by_shader_type(candidate_obj, "PUPIL")
        if brow_material is None:
            brow_material = _find_material_by_shader_type(candidate_obj, "BROW")
        if iris_material is not None and brow_material is not None:
            break

    if iris_material is None:
        iris_material = _find_material_slot(obj, ("iris", "eye", "pupil", "eyel"))
    if brow_material is None:
        brow_material = _find_material_slot(obj, ("brow", "lash", "eyelash", "眉", "睫"))
        if brow_material is not None and _detect_shader_type_from_material(brow_material) == "PUPIL":
            brow_material = None

    for related in related_objects:
        if iris_material is None:
            iris_material = _find_material_slot(related, ("iris", "eye", "eyel", "pupil"))
        if brow_material is None:
            brow_material = _find_material_slot(related, ("brow", "lash", "eyelash", "眉", "睫"))
            if brow_material is not None and _detect_shader_type_from_material(brow_material) == "PUPIL":
                brow_material = None
        if iris_material is not None and brow_material is not None:
            break

    iris_material = iris_material or support_materials.get("iris")

    source_brow_material = support_materials.get("brow")
    if source_brow_material is not None:
        if brow_material is None:
            brow_material = source_brow_material
        elif brow_material == iris_material:
            brow_material = source_brow_material
        elif _detect_shader_type_from_material(brow_material) != "BROW":
            brow_material = source_brow_material
        elif "__OLD" in brow_material.name:
            brow_material = source_brow_material
    else:
        brow_material = brow_material or source_brow_material

    iris_alpha = _copy_alpha_template(settings, "IRIS", iris_material, f"{iris_material.name}_AlphaProxy") if iris_material else support_materials.get("iris_alpha")
    brow_alpha = _copy_alpha_template(settings, "BROW", brow_material, f"{brow_material.name}_AlphaProxy") if brow_material else support_materials.get("brow_alpha")
    return {
        "face": face_material,
        "iris": iris_material,
        "brow": brow_material,
        "iris_alpha": iris_alpha,
        "brow_alpha": brow_alpha,
    }


def _configure_eye_transparency_modifier(target_obj, eye_group, bundle, modifier_name=None):
    if target_obj is None or eye_group is None:
        return None
    modifier_name = modifier_name or EYE_TRANSPARENCY_MODIFIER_PREFIX
    if bundle.get("iris") is None and bundle.get("brow") is None:
        _remove_modifier_by_name(target_obj, modifier_name)
        return None

    eye_mod = _attach_named_geo_modifier(target_obj, eye_group, modifier_name)
    _move_modifier_before_outline(target_obj, eye_mod)
    _set_modifier_input(eye_mod, "irisMat", bundle.get("iris"))
    _set_modifier_input(eye_mod, "browMat", bundle.get("brow"))
    _set_modifier_input(eye_mod, "irisAlphaMat", bundle.get("iris_alpha"))
    _set_modifier_input(eye_mod, "browAlphaMat", bundle.get("brow_alpha"))
    return eye_mod


def _configure_smooth_outline_modifier(modifier, outline_material, base_material, st_image, width):
    _set_modifier_input(modifier, "描边宽度", width)
    _set_modifier_input(modifier, "描边材质", outline_material)
    _set_modifier_input(modifier, "使用顶点色控制", False)
    _set_modifier_input(modifier, "_ST", st_image)
    _set_modifier_input(modifier, "使用ST", bool(st_image))
    _set_modifier_input(modifier, "Use material filtering", False)
    _set_modifier_input(modifier, "The material of the object using outline", base_material)


def _remove_face_subdivision_modifier(obj):
    modifier = obj.modifiers.get("Subdivision")
    if modifier is not None and modifier.type == "SUBSURF":
        obj.modifiers.remove(modifier)


def _iter_face_integrated_eye_entries(settings, source_material_map):
    for item in settings.face_iris_materials:
        source_material = item.source_material
        if source_material is None:
            continue
        source_key = source_material.as_pointer()
        for target_material in source_material_map.get(source_key, []):
            yield "IRIS", target_material
    for item in settings.face_brow_materials:
        source_material = item.source_material
        if source_material is None:
            continue
        source_key = source_material.as_pointer()
        for target_material in source_material_map.get(source_key, []):
            yield "BROW", target_material


def _ensure_face_integrated_eye_node_group(obj, iris_pairs, brow_pairs):
    group_name = f"Endfield Face Eye Transparency {obj.name}"
    group = bpy.data.node_groups.get(group_name)
    if not (group and group.bl_idname == "GeometryNodeTree"):
        group = bpy.data.node_groups.new(group_name, "GeometryNodeTree")

    interface = group.interface
    while interface.items_tree:
        interface.remove(interface.items_tree[0])
    interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    nodes = group.nodes
    links = group.links
    nodes.clear()

    group_input = nodes.new("NodeGroupInput")
    group_output = nodes.new("NodeGroupOutput")
    active_camera = nodes.new("GeometryNodeInputActiveCamera")
    object_info = nodes.new("GeometryNodeObjectInfo")
    position = nodes.new("GeometryNodeInputPosition")
    vec_sub = nodes.new("ShaderNodeVectorMath")
    vec_norm = nodes.new("ShaderNodeVectorMath")
    vec_scale = nodes.new("ShaderNodeVectorMath")
    geo_to_instances = nodes.new("GeometryNodeGeometryToInstance")
    join_geometry = nodes.new("GeometryNodeJoinGeometry")

    vec_sub.operation = "SUBTRACT"
    vec_norm.operation = "NORMALIZE"
    vec_scale.operation = "SCALE"
    if "Scale" in vec_scale.inputs:
        vec_scale.inputs["Scale"].default_value = 0.1

    group_input.location = (-1200.0, 0.0)
    active_camera.location = (-1200.0, -260.0)
    object_info.location = (-980.0, -260.0)
    position.location = (-980.0, -40.0)
    vec_sub.location = (-760.0, -140.0)
    vec_norm.location = (-540.0, -140.0)
    vec_scale.location = (-320.0, -140.0)
    geo_to_instances.location = (360.0, -120.0)
    join_geometry.location = (620.0, 0.0)
    group_output.location = (860.0, 0.0)

    links.new(active_camera.outputs["Active Camera"], object_info.inputs["Object"])
    links.new(object_info.outputs["Location"], vec_sub.inputs[0])
    links.new(position.outputs["Position"], vec_sub.inputs[1])
    links.new(vec_sub.outputs["Vector"], vec_norm.inputs[0])
    links.new(vec_norm.outputs["Vector"], vec_scale.inputs[0])
    links.new(group_input.outputs["Geometry"], join_geometry.inputs["Geometry"])
    links.new(geo_to_instances.outputs["Instances"], join_geometry.inputs["Geometry"])
    links.new(join_geometry.outputs["Geometry"], group_output.inputs["Geometry"])

    y = 120.0
    step = -260.0

    def add_branch(base_material, alpha_material, label):
        nonlocal y
        selection = nodes.new("GeometryNodeMaterialSelection")
        set_position = nodes.new("GeometryNodeSetPosition")
        replace_material = nodes.new("GeometryNodeReplaceMaterial")

        selection.location = (-320.0, y)
        set_position.location = (-80.0, y)
        replace_material.location = (160.0, y)
        selection.label = label

        try:
            selection.inputs["Material"].default_value = base_material
        except Exception:
            pass
        try:
            replace_material.inputs["Old"].default_value = base_material
        except Exception:
            pass
        try:
            replace_material.inputs["New"].default_value = alpha_material
        except Exception:
            pass

        links.new(group_input.outputs["Geometry"], set_position.inputs["Geometry"])
        links.new(selection.outputs["Selection"], set_position.inputs["Selection"])
        links.new(vec_scale.outputs["Vector"], set_position.inputs["Offset"])
        links.new(set_position.outputs["Geometry"], replace_material.inputs["Geometry"])
        links.new(replace_material.outputs["Geometry"], geo_to_instances.inputs["Geometry"])
        y += step

    for index, (base_material, alpha_material) in enumerate(iris_pairs, start=1):
        add_branch(base_material, alpha_material, f"Iris {index}")
    for index, (base_material, alpha_material) in enumerate(brow_pairs, start=1):
        add_branch(base_material, alpha_material, f"Brow {index}")

    return group


def _configure_face_integrated_eye_modifiers(settings, obj, library, source_material_map):
    warning = False
    attr_mod = None
    eye_modifiers = []

    if not settings.face_integrated_eye_transparency:
        _remove_modifier_by_name(obj, "Endfield Eye Attribute Patch")
        return warning, attr_mod, eye_modifiers

    attr_group = _ensure_eye_attribute_patch_node_group()
    if attr_group:
        attr_mod = _attach_geo_modifier(obj, attr_group, attr_group.name)
    else:
        warning = True

    _remove_eye_transparency_modifiers(obj)

    configured_entries = list(_iter_face_integrated_eye_entries(settings, source_material_map))
    if not configured_entries:
        return warning, attr_mod, eye_modifiers

    iris_pairs = []
    brow_pairs = []
    for role, target_material in configured_entries:
        if role == "BROW":
            alpha_material = _copy_alpha_template(settings, "BROW", target_material, f"{target_material.name}_AlphaProxy")
            brow_pairs.append((target_material, alpha_material))
        else:
            alpha_material = _copy_alpha_template(settings, "IRIS", target_material, f"{target_material.name}_AlphaProxy")
            iris_pairs.append((target_material, alpha_material))

    if not iris_pairs and not brow_pairs:
        return warning, attr_mod, eye_modifiers

    eye_group = _ensure_face_integrated_eye_node_group(obj, iris_pairs, brow_pairs)
    eye_mod = _attach_named_geo_modifier(obj, eye_group, EYE_TRANSPARENCY_MODIFIER_PREFIX)
    _move_modifier_before_outline(obj, eye_mod)
    eye_modifiers.append(eye_mod)

    return warning, attr_mod, eye_modifiers


def _configure_face_modifiers(settings, obj, face_material, outline_material, helper_rig, library, loaded_images, source_material_map=None):
    warning = False
    sun_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["SUN_VEC"])
    sun_mod = obj.modifiers.get(sun_group.name) if sun_group else None
    vector_mod = None
    smooth_mod = None
    raycast_mod = None

    vector_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["FACE_VECTOR"])
    if vector_group:
        vector_mod = _attach_geo_modifier(obj, vector_group, vector_group.name)
        _set_modifier_input(vector_mod, "HC", helper_rig["HC"])
        _set_modifier_input(vector_mod, "HF", helper_rig["HF"])
        _set_modifier_input(vector_mod, "HR", helper_rig["HR"])
        _set_modifier_input(vector_mod, "only need HeadForward", False)
    else:
        warning = True

    smooth_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["SMOOTH_OUTLINE"])
    if smooth_group:
        smooth_mod = _attach_geo_modifier(obj, smooth_group, smooth_group.name)
        _configure_smooth_outline_modifier(
            smooth_mod,
            outline_material,
            None,
            loaded_images.get("tex_st"),
            settings.outline_thickness,
        )
    else:
        warning = True

    raycast_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["FACE_RAYCAST"])
    if raycast_group:
        raycast_mod = _attach_geo_modifier(obj, raycast_group, raycast_group.name)
        _set_modifier_input(raycast_mod, "FaceMat", face_material)
    else:
        warning = True

    attr_mod = None
    eye_modifiers = []
    if settings.face_integrated_eye_transparency:
        face_eye_warning, attr_mod, eye_modifiers = _configure_face_integrated_eye_modifiers(
            settings,
            obj,
            library,
            source_material_map or {},
        )
        warning = warning or face_eye_warning
    else:
        _remove_modifier_by_name(obj, "Endfield Eye Attribute Patch")
        _remove_eye_transparency_modifiers(obj)

    _remove_face_subdivision_modifier(obj)
    _ensure_modifier_sequence(obj, [sun_mod, vector_mod, smooth_mod, raycast_mod, attr_mod, *eye_modifiers])
    return warning


def _configure_eye_object_modifiers(settings, obj, eye_material, library):
    warning = False
    support_materials = _ensure_eye_support_materials(settings, obj)
    sun_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["SUN_VEC"])
    sun_mod = obj.modifiers.get(sun_group.name) if sun_group else None
    helper_rig = _current_head_helper_rig()
    vector_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["FACE_VECTOR"])
    vector_mod = None
    attr_mod = None
    if vector_group and helper_rig is not None:
        vector_mod = _attach_geo_modifier(obj, vector_group, vector_group.name)
        _set_modifier_input(vector_mod, "HC", helper_rig["HC"])
        _set_modifier_input(vector_mod, "HF", helper_rig["HF"])
        _set_modifier_input(vector_mod, "HR", helper_rig["HR"])
        _set_modifier_input(vector_mod, "only need HeadForward", True)
    else:
        warning = True

    attr_group = _ensure_eye_attribute_patch_node_group()
    if attr_group:
        attr_mod = _attach_geo_modifier(obj, attr_group, attr_group.name)
    else:
        warning = True

    eye_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["EYE_TRANSPARENCY"])
    eye_mod = None
    if eye_group:
        eye_mod = _configure_eye_transparency_modifier(
            obj,
            eye_group,
            _ensure_face_material_bundle(settings, obj, eye_material, support_materials=support_materials),
        )
        if eye_mod is None:
            warning = True
    else:
        warning = True
    _ensure_modifier_sequence(obj, [sun_mod, vector_mod, attr_mod, eye_mod])
    return warning


def _configure_hair_modifiers(settings, obj, library):
    warning = False
    smooth_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["SMOOTH_OUTLINE"])
    if smooth_group:
        smooth_mod = _attach_geo_modifier(obj, smooth_group, smooth_group.name)
        _configure_smooth_outline_modifier(
            smooth_mod,
            obj.material_slots[1].material if len(obj.material_slots) > 1 else None,
            obj.material_slots[0].material if len(obj.material_slots) > 0 else None,
            None,
            settings.outline_thickness,
        )
        _move_modifier_before_outline(obj, smooth_mod)
    else:
        warning = True

    shadow_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["SHADOW_PROXY"])
    if shadow_group:
        shadow_mod = _attach_geo_modifier(obj, shadow_group, shadow_group.name)
        _move_modifier_after_outline(obj, shadow_mod)
        _set_modifier_input(shadow_mod, "Shadow Proxy", _ensure_shadow_proxy_material(settings))
        _set_modifier_input(shadow_mod, "Pos Offset", -0.38)
        _set_modifier_input(shadow_mod, "Pos Debug", False)
    else:
        warning = True
    return warning


def _configure_surface_outline_modifiers(settings, obj, primary_material, outline_material, library, loaded_images, include_time=False):
    warning = False
    weld_mod = None
    if getattr(settings, "shader_type", "") == "BODY":
        weld_mod = _ensure_body_weld_modifier(obj)

    smooth_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["SMOOTH_OUTLINE"])
    smooth_mod = None
    time_mod = None
    if smooth_group:
        smooth_mod = _attach_geo_modifier(obj, smooth_group, smooth_group.name)
        _configure_smooth_outline_modifier(
            smooth_mod,
            outline_material,
            primary_material,
            loaded_images.get("tex_st"),
            settings.outline_thickness,
        )
    else:
        warning = True

    if include_time:
        time_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["TIME_SETUP"])
        if time_group:
            time_mod = _attach_geo_modifier(obj, time_group, time_group.name)
        else:
            warning = True

    _ensure_modifier_sequence(obj, [weld_mod, obj.modifiers.get(GEOMETRY_NODE_PREFS["SUN_VEC"][0]), smooth_mod, time_mod])
    return warning


def _configure_common_geo_modifier(obj, library):
    group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["SUN_VEC"])
    if not group:
        return True
    lf = _find_matching_object(SUN_HELPER_LF_NAME)
    lc = _find_matching_object(SUN_HELPER_LC_NAME)
    if lf is None or lc is None:
        return True
    _rebind_sun_vec_targets(group, lf, lc)
    modifier = _attach_geo_modifier(obj, group, group.name)
    _move_modifier_before_outline(obj, modifier)
    return False


def _is_outline_like(material) -> bool:
    if not material:
        return False
    name = material.name.lower()
    return "outline" in name or "shadow proxy" in name or name.startswith("mmd_edge.")


def _slot_indices_for_object(obj, settings: ENDFIELD_PG_Settings):
    if len(obj.material_slots) == 0:
        obj.data.materials.append(None)

    selected_eye_materials = {
        item.source_material
        for item in [*getattr(settings, "face_iris_materials", []), *getattr(settings, "face_brow_materials", [])]
        if item.source_material is not None
    }
    extra_indices = set()
    if settings.shader_type == "FACE" and settings.face_integrated_eye_transparency and selected_eye_materials:
        for index, slot in enumerate(obj.material_slots):
            if slot.material in selected_eye_materials:
                extra_indices.add(index)

    if settings.apply_mode == "ALL_SLOTS":
        indices = []
        for index, slot in enumerate(obj.material_slots):
            if _is_outline_like(slot.material):
                continue
            indices.append(index)
        indices.extend(sorted(extra_indices))
        return sorted(set(indices)) or [0]
    indices = {max(0, obj.active_material_index), *extra_indices}
    return sorted(indices)


def _detect_shader_type_from_material(material):
    node = _find_main_shader_node(material)
    if node is None or not node.node_tree:
        return None
    name = node.node_tree.name
    if "BaseHair" in name:
        return "HAIR"
    if "FaceBase" in name or "BaseFace" in name:
        return "FACE"
    if "irisBase" in name:
        return "PUPIL"
    if "BaseBrow" in name:
        return "BROW"
    if "PBRToonBase" in name:
        return "BODY" if "body" in material.name.lower() else "CLOTH" if "cloth" in material.name.lower() else "BODY"
    return None


def _find_main_shader_node(material):
    if not material or not material.use_nodes or not material.node_tree:
        return None
    groups = [node for node in material.node_tree.nodes if node.type == "GROUP" and node.node_tree]
    for shader_type in ("FACE", "HAIR", "PUPIL", "BROW", "BODY", "CLOTH"):
        for node in groups:
            if any(keyword in node.node_tree.name for keyword in SHADER_GROUP_KEYWORDS[shader_type]):
                return node
    return None


def _find_face_sdf_image_nodes(node_tree):
    if not node_tree:
        return []
    results = []
    for node in node_tree.nodes:
        if node.type != "TEX_IMAGE":
            continue
        image = getattr(node, "image", None)
        image_name = image.name.lower() if image else ""
        node_name = f"{node.name} {node.label}".lower()
        if "common_female_face_01_sdf" in image_name or "face_01_sdf" in image_name or "sdf" in node_name:
            results.append(node)
    return results


def _find_face_cm_image_nodes(node_tree):
    if not node_tree:
        return []
    results = []
    for node in node_tree.nodes:
        if node.type != "TEX_IMAGE":
            continue
        image = getattr(node, "image", None)
        image_name = image.name.lower() if image else ""
        node_name = f"{node.name} {node.label}".lower()
        if "common_female_face_01_cm_m" in image_name or "cm_m" in node_name:
            results.append(node)
    return results


def _ensure_local_face_shader_group(material):
    shader_node = _find_main_shader_node(material)
    if shader_node is None or not shader_node.node_tree:
        return None
    if _detect_shader_type_from_material(material) != "FACE":
        return shader_node.node_tree
    node_tree = shader_node.node_tree
    if node_tree.get("_endfield_face_group_local"):
        return node_tree
    localized = node_tree.copy()
    localized["_endfield_face_group_local"] = True
    localized["_endfield_face_group_source"] = node_tree.name
    shader_node.node_tree = localized
    return localized


def _ensure_face_sdf_mapping_controls(material):
    node_tree = _ensure_local_face_shader_group(material)
    if not node_tree:
        return None

    sdf_nodes = _find_face_sdf_image_nodes(node_tree)
    if not sdf_nodes:
        return None

    mapping_name = "ENDFIELD_FACE_SDF_MAPPING"
    mapping_node = node_tree.nodes.get(mapping_name)
    if mapping_node and mapping_node.bl_idname != "ShaderNodeMapping":
        node_tree.nodes.remove(mapping_node)
        mapping_node = None

    for tex_node in sdf_nodes:
        vector_input = tex_node.inputs.get("Vector")
        if vector_input is None:
            continue
        source_socket = None
        if vector_input.is_linked:
            link = vector_input.links[0]
            if link.from_node == mapping_node:
                continue
            source_socket = link.from_socket
            node_tree.links.remove(link)
        if mapping_node is None:
            mapping_node = node_tree.nodes.new("ShaderNodeMapping")
            mapping_node.name = mapping_name
            mapping_node.label = "Face SDF Mapping"
            mapping_node.location = (tex_node.location.x - 220.0, tex_node.location.y)
            if hasattr(mapping_node, "vector_type"):
                mapping_node.vector_type = "POINT"
        if source_socket is not None and not mapping_node.inputs["Vector"].is_linked:
            node_tree.links.new(source_socket, mapping_node.inputs["Vector"])
        if not vector_input.is_linked:
            node_tree.links.new(mapping_node.outputs["Vector"], vector_input)

    return mapping_node


def _ensure_face_cm_mapping_controls(material):
    node_tree = _ensure_local_face_shader_group(material)
    if not node_tree:
        return None

    cm_nodes = _find_face_cm_image_nodes(node_tree)
    if not cm_nodes:
        return None

    mapping_name = "ENDFIELD_FACE_CM_MAPPING"
    uv_name = "ENDFIELD_FACE_CM_UV"
    mapping_node = node_tree.nodes.get(mapping_name)
    if mapping_node and mapping_node.bl_idname != "ShaderNodeMapping":
        node_tree.nodes.remove(mapping_node)
        mapping_node = None

    uv_node = node_tree.nodes.get(uv_name)
    if uv_node and uv_node.bl_idname != "ShaderNodeUVMap":
        node_tree.nodes.remove(uv_node)
        uv_node = None

    for tex_node in cm_nodes:
        vector_input = tex_node.inputs.get("Vector")
        if vector_input is None:
            continue
        source_socket = None
        if vector_input.is_linked:
            link = vector_input.links[0]
            if link.from_node == mapping_node:
                continue
            source_socket = link.from_socket
            node_tree.links.remove(link)
        if uv_node is None:
            uv_node = node_tree.nodes.new("ShaderNodeUVMap")
            uv_node.name = uv_name
            uv_node.label = "Face CM UV"
            uv_node.location = (tex_node.location.x - 440.0, tex_node.location.y)
        if mapping_node is None:
            mapping_node = node_tree.nodes.new("ShaderNodeMapping")
            mapping_node.name = mapping_name
            mapping_node.label = "Face CM Mapping"
            mapping_node.location = (tex_node.location.x - 220.0, tex_node.location.y)
            if hasattr(mapping_node, "vector_type"):
                mapping_node.vector_type = "POINT"
        if source_socket is None:
            source_socket = uv_node.outputs.get("UV")
        if source_socket is not None and not mapping_node.inputs["Vector"].is_linked:
            node_tree.links.new(source_socket, mapping_node.inputs["Vector"])
        if not vector_input.is_linked:
            node_tree.links.new(mapping_node.outputs["Vector"], vector_input)

    return mapping_node


def _face_sdf_mapping_node(material):
    shader_node = _find_main_shader_node(material)
    if shader_node is None or not shader_node.node_tree:
        return None
    node_tree = shader_node.node_tree
    mapping = node_tree.nodes.get("ENDFIELD_FACE_SDF_MAPPING")
    if mapping and mapping.bl_idname == "ShaderNodeMapping":
        return mapping
    return None


def _face_cm_mapping_node(material):
    shader_node = _find_main_shader_node(material)
    if shader_node is None or not shader_node.node_tree:
        return None
    node_tree = shader_node.node_tree
    mapping = node_tree.nodes.get("ENDFIELD_FACE_CM_MAPPING")
    if mapping and mapping.bl_idname == "ShaderNodeMapping":
        return mapping
    return None


def _ensure_face_mapping_node(material, target: str):
    if target == "SDF":
        return _ensure_face_sdf_mapping_controls(material)
    if target == "CM":
        return _ensure_face_cm_mapping_controls(material)
    return None


def _adjust_face_mapping(material, target: str, socket_name: str, index: int, delta: float):
    mapping_node = _ensure_face_mapping_node(material, target)
    if mapping_node is None:
        return None
    socket = mapping_node.inputs.get(socket_name)
    if socket is None or not hasattr(socket, "default_value"):
        return None
    values = list(socket.default_value)
    if index >= len(values):
        return None
    values[index] += delta
    socket.default_value = values
    return mapping_node


def _selected_test_meshes(context):
    meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]
    if meshes:
        return meshes
    if context.active_object and context.active_object.type == "MESH":
        return [context.active_object]
    return []


def _outline_anchor_index(obj):
    smooth_outline_names = set(GEOMETRY_NODE_PREFS["SMOOTH_OUTLINE"])
    for index, modifier in enumerate(obj.modifiers):
        if modifier.type == "SOLIDIFY":
            return index
        if modifier.type == "NODES" and modifier.node_group and modifier.node_group.name in smooth_outline_names:
            return index
    return None


def _move_modifier_before_outline(obj, modifier):
    if modifier is None:
        return
    current_index = obj.modifiers.find(modifier.name)
    if current_index < 0:
        return
    anchor_index = _outline_anchor_index(obj)
    if anchor_index is None:
        return
    if current_index > anchor_index:
        obj.modifiers.move(current_index, anchor_index)


def _move_modifier_after_outline(obj, modifier):
    if modifier is None:
        return
    current_index = obj.modifiers.find(modifier.name)
    if current_index < 0:
        return
    anchor_index = _outline_anchor_index(obj)
    if anchor_index is None:
        return
    target_index = min(anchor_index + 1, len(obj.modifiers) - 1)
    if current_index != target_index:
        obj.modifiers.move(current_index, target_index)


def _ensure_test_weld_modifier(obj, distance: float):
    modifier = obj.modifiers.get(TEST_WELD_MODIFIER_NAME)
    if modifier is None or modifier.type != "WELD":
        modifier = obj.modifiers.new(TEST_WELD_MODIFIER_NAME, "WELD")
    if hasattr(modifier, "merge_threshold"):
        modifier.merge_threshold = distance
    if hasattr(modifier, "mode"):
        try:
            modifier.mode = "ALL"
        except Exception:
            pass
    _move_modifier_before_outline(obj, modifier)
    return modifier


def _ensure_body_weld_modifier(obj):
    modifier = obj.modifiers.get(BODY_WELD_MODIFIER_NAME)
    if modifier is None or modifier.type != "WELD":
        modifier = obj.modifiers.new(BODY_WELD_MODIFIER_NAME, "WELD")
    modifier.name = BODY_WELD_MODIFIER_NAME
    if hasattr(modifier, "merge_threshold"):
        modifier.merge_threshold = BODY_WELD_DISTANCE
    if hasattr(modifier, "mode"):
        try:
            modifier.mode = "ALL"
        except Exception:
            pass
    if hasattr(modifier, "loose_edges"):
        modifier.loose_edges = False
    return modifier


def _ensure_test_merge_node_group():
    group = bpy.data.node_groups.get(TEST_GN_MERGE_GROUP_NAME)
    if group and group.bl_idname == "GeometryNodeTree":
        return group

    group = bpy.data.node_groups.new(TEST_GN_MERGE_GROUP_NAME, "GeometryNodeTree")
    interface = group.interface
    interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    interface.new_socket(name="Distance", in_out="INPUT", socket_type="NodeSocketFloat")
    interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    nodes = group.nodes
    links = group.links
    nodes.clear()

    group_input = nodes.new("NodeGroupInput")
    merge = nodes.new("GeometryNodeMergeByDistance")
    group_output = nodes.new("NodeGroupOutput")

    group_input.location = (-260.0, 0.0)
    merge.location = (0.0, 0.0)
    group_output.location = (240.0, 0.0)

    links.new(group_input.outputs["Geometry"], merge.inputs["Geometry"])
    if "Distance" in group_input.outputs and "Distance" in merge.inputs:
        links.new(group_input.outputs["Distance"], merge.inputs["Distance"])
    links.new(merge.outputs["Geometry"], group_output.inputs["Geometry"])
    return group


def _ensure_test_gn_merge_modifier(obj, distance: float):
    node_group = _ensure_test_merge_node_group()
    modifier = obj.modifiers.get(TEST_GN_MERGE_MODIFIER_NAME)
    if modifier is None or modifier.type != "NODES":
        modifier = obj.modifiers.new(TEST_GN_MERGE_MODIFIER_NAME, "NODES")
    modifier.node_group = node_group
    _set_modifier_input(modifier, "Distance", distance)
    _move_modifier_before_outline(obj, modifier)
    return modifier


def _ensure_eye_attribute_patch_node_group():
    group_name = "Endfield Eye Attribute Patch"
    group = bpy.data.node_groups.get(group_name)
    if not (group and group.bl_idname == "GeometryNodeTree"):
        group = bpy.data.node_groups.new(group_name, "GeometryNodeTree")
        interface = group.interface
        interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

        nodes = group.nodes
        links = group.links
        nodes.clear()

        group_input = nodes.new("NodeGroupInput")
        store_eyes = nodes.new("GeometryNodeStoreNamedAttribute")
        group_output = nodes.new("NodeGroupOutput")

        group_input.location = (-260.0, 0.0)
        store_eyes.location = (0.0, 0.0)
        group_output.location = (240.0, 0.0)

        links.new(group_input.outputs["Geometry"], store_eyes.inputs["Geometry"])
        links.new(store_eyes.outputs["Geometry"], group_output.inputs["Geometry"])

    store_eyes = next((node for node in group.nodes if node.bl_idname == "GeometryNodeStoreNamedAttribute"), None)
    if store_eyes is None:
        return group

    store_eyes.data_type = "FLOAT"
    store_eyes.domain = "POINT"
    if "Name" in store_eyes.inputs:
        store_eyes.inputs["Name"].default_value = "Eyes"
    if "Selection" in store_eyes.inputs:
        store_eyes.inputs["Selection"].default_value = True
    if "Value" in store_eyes.inputs:
        store_eyes.inputs["Value"].default_value = 0.0

    return group


def _is_chen_source_image(image) -> bool:
    if image is None:
        return False
    name = image.name.lower()
    filepath = bpy.path.abspath(image.filepath).lower() if image.filepath else ""
    chen_markers = ("t_actor_chen", "m_actor_chen", "chen_")
    return any(marker in name or marker in filepath for marker in chen_markers)


def _cleanup_unused_source_assets(library_path: str):
    stamp = _library_stamp(library_path)

    for material in list(bpy.data.materials):
        if material.users != 0:
            continue
        if stamp and material.get(SOURCE_LIBRARY_STAMP_KEY) == stamp:
            bpy.data.materials.remove(material)

    for image in list(bpy.data.images):
        if image.users != 0:
            continue
        if _is_chen_source_image(image):
            bpy.data.images.remove(image)


@persistent
def _endfield_load_post(_dummy=None):
    try:
        _ensure_eye_attribute_patch_node_group()
    except Exception:
        pass


def _ensure_proxy_outline_material(settings: ENDFIELD_PG_Settings, source_obj, base_material=None, loaded_images=None, name_override: str = ""):
    loaded_images = dict(loaded_images or _load_images_from_settings(settings))
    material = _ensure_outline_material_instance(
        settings,
        source_obj,
        base_material,
        loaded_images,
        name_override=name_override or TEST_PROXY_MATERIAL_NAME,
    )
    if hasattr(material, "use_backface_culling"):
        material.use_backface_culling = False
    if hasattr(material, "shadow_method"):
        try:
            material.shadow_method = "NONE"
        except Exception:
            pass
    return material


def _remove_object_and_data(obj):
    if obj is None:
        return
    mesh_data = obj.data if obj.type == "MESH" else None
    bpy.data.objects.remove(obj, do_unlink=True)
    if mesh_data and mesh_data.users == 0:
        bpy.data.meshes.remove(mesh_data)


def _prepare_proxy_modifiers(proxy_obj):
    keep_types = {"ARMATURE", "MIRROR", "LATTICE", "SUBSURF", "MESH_DEFORM", "SURFACE_DEFORM", "CORRECTIVE_SMOOTH"}
    for modifier in list(proxy_obj.modifiers):
        if modifier.type not in keep_types:
            proxy_obj.modifiers.remove(modifier)


def _ensure_proxy_material_slots(proxy_obj, settings: ENDFIELD_PG_Settings, source_obj):
    original_materials = [slot.material for slot in proxy_obj.material_slots]
    fallback_base = None
    if source_obj is not None and source_obj.active_material and not _is_outline_like(source_obj.active_material):
        fallback_base = source_obj.active_material
    if fallback_base is None:
        fallback_base = next((material for material in original_materials if material and not _is_outline_like(material)), None)
    if fallback_base is None:
        fallback_base = _ensure_template_material(settings)

    base_materials = []
    old_to_new = {}
    for index, material in enumerate(original_materials):
        if material is None:
            material = fallback_base
        if _is_outline_like(material):
            continue
        old_to_new[index] = len(base_materials)
        base_materials.append(material)

    if not base_materials:
        base_materials = [fallback_base]

    remapped_indices = []
    if hasattr(proxy_obj.data, "polygons"):
        remapped_indices = [old_to_new.get(polygon.material_index, 0) for polygon in proxy_obj.data.polygons]

    proxy_obj.data.materials.clear()
    outline_materials = []
    default_images = _load_images_from_settings(settings)

    for index, base_material in enumerate(base_materials):
        proxy_obj.data.materials.append(base_material)
        slot_images = dict(default_images)
        slot_images.update(_extract_loaded_images_from_material(base_material, settings.shader_type))
        outline_material = _ensure_proxy_outline_material(
            settings,
            proxy_obj,
            base_material,
            loaded_images=slot_images,
            name_override=f"{TEST_PROXY_MATERIAL_NAME}_{index:02d}_{base_material.name}",
        )
        outline_materials.append(outline_material)

    for outline_material in outline_materials:
        proxy_obj.data.materials.append(outline_material)

    if remapped_indices:
        for polygon, material_index in zip(proxy_obj.data.polygons, remapped_indices):
            polygon.material_index = material_index

    return len(base_materials)


def _ensure_proxy_solidify(proxy_obj, settings: ENDFIELD_PG_Settings, material_offset: int):
    modifier = proxy_obj.modifiers.get(settings.outline_modifier_name)
    if modifier is None or modifier.type != "SOLIDIFY":
        modifier = proxy_obj.modifiers.new(settings.outline_modifier_name, "SOLIDIFY")
    modifier.thickness = settings.outline_thickness
    if hasattr(modifier, "offset"):
        modifier.offset = 1.0
    if hasattr(modifier, "use_flip_normals"):
        modifier.use_flip_normals = True
    if hasattr(modifier, "use_rim_only"):
        modifier.use_rim_only = True
    if hasattr(modifier, "use_rim"):
        modifier.use_rim = True
    if hasattr(modifier, "material_offset"):
        modifier.material_offset = material_offset
    return modifier


def _create_or_update_outline_proxy(context, settings: ENDFIELD_PG_Settings, objects):
    if not objects:
        return None

    active_source = context.view_layer.objects.active if context.view_layer.objects.active in objects else objects[0]
    proxy_name = f"{active_source.name}{TEST_PROXY_SUFFIX}"
    existing_proxy = bpy.data.objects.get(proxy_name)
    if existing_proxy is not None:
        _remove_object_and_data(existing_proxy)

    view_layer = context.view_layer
    previous_active = view_layer.objects.active
    previous_selected = [obj for obj in context.selected_objects]

    try:
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")

        duplicates = []
        active_duplicate = None
        for source in objects:
            duplicate = source.copy()
            duplicate.data = source.data.copy()
            duplicate.animation_data_clear()
            for collection in source.users_collection:
                _link_object_to_collection(duplicate, collection)
            duplicate.select_set(True)
            duplicates.append(duplicate)
            if source == active_source:
                active_duplicate = duplicate

        view_layer.objects.active = active_duplicate
        if len(duplicates) > 1 and bpy.ops.object.join.poll():
            bpy.ops.object.join()
            proxy_obj = view_layer.objects.active
        else:
            proxy_obj = active_duplicate

        proxy_obj.name = proxy_name
        proxy_obj.data.name = f"{proxy_name}_Mesh"
        _prepare_proxy_modifiers(proxy_obj)
        material_offset = _ensure_proxy_material_slots(proxy_obj, settings, active_source)
        _ensure_test_weld_modifier(proxy_obj, settings.test_weld_distance)
        _ensure_test_gn_merge_modifier(proxy_obj, settings.test_gn_merge_distance)
        _ensure_proxy_solidify(proxy_obj, settings, material_offset)
        return proxy_obj
    finally:
        bpy.ops.object.select_all(action="DESELECT")
        for selected in previous_selected:
            if selected.name in bpy.data.objects:
                bpy.data.objects[selected.name].select_set(True)
        if previous_active and previous_active.name in bpy.data.objects:
            view_layer.objects.active = bpy.data.objects[previous_active.name]


class ENDFIELD_OT_TestOutlineWeld(Operator):
    bl_idname = "endfield_toon.test_outline_weld"
    bl_label = "A：Weld描边"
    bl_description = "给选中网格添加非破坏性 Weld 修改器，用于描边缝隙修复"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return bool(_selected_test_meshes(context))

    def execute(self, context):
        settings = context.scene.endfield_toon_settings
        objects = _selected_test_meshes(context)
        for obj in objects:
            _ensure_test_weld_modifier(obj, settings.test_weld_distance)
        self.report({"INFO"}, f"已为 {len(objects)} 个网格添加焊接修改器 ")
        return {"FINISHED"}


class ENDFIELD_OT_TestOutlineProxy(Operator):
    bl_idname = "endfield_toon.test_outline_proxy"
    bl_label = "B：Outline Proxy"
    bl_description = "基于当前选中网格创建非破坏性描边代理对象"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return bool(_selected_test_meshes(context))

    def execute(self, context):
        settings = context.scene.endfield_toon_settings
        objects = _selected_test_meshes(context)
        proxy_obj = _create_or_update_outline_proxy(context, settings, objects)
        if proxy_obj is None:
            self.report({"WARNING"}, "未能创建描边代理")
            return {"CANCELLED"}
        self.report({"INFO"}, f"已创建描边代理：{proxy_obj.name}")
        return {"FINISHED"}


class ENDFIELD_OT_TestOutlineGNMerge(Operator):
    bl_idname = "endfield_toon.test_outline_gn_merge"
    bl_label = "C：GN合并描边"
    bl_description = "给选中网格添加 Geometry Nodes Merge by Distance 修改器"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return bool(_selected_test_meshes(context))

    def execute(self, context):
        settings = context.scene.endfield_toon_settings
        objects = _selected_test_meshes(context)
        for obj in objects:
            _ensure_test_gn_merge_modifier(obj, settings.test_gn_merge_distance)
        self.report({"INFO"}, f"已为 {len(objects)} 个网格添加 GN 合并")
        return {"FINISHED"}


class ENDFIELD_OT_AutoFillTextures(Operator):
    bl_idname = "endfield_toon.autofill_textures"
    bl_label = "按_D自动补全贴图"
    bl_description = "根据_D贴图自动推断其它贴图"

    def execute(self, context):
        settings = context.scene.endfield_toon_settings
        if not settings.tex_d:
            self.report({"WARNING"}, "请先选择 _D.png")
            return {"CANCELLED"}

        filled = _autofill_missing_texture_paths(settings)
        self.report({"INFO"}, f"已自动补全 {filled} 个贴图槽")
        return {"FINISHED"}


class ENDFIELD_OT_AddFaceEyeMaterialSlot(Operator):
    bl_idname = "endfield_toon.add_face_eye_material_slot"
    bl_label = "添加眼透材质"
    bl_description = "为脸眼一体模式添加一个需要眼透的材质槽"
    bl_options = {"REGISTER", "UNDO"}

    target_group: EnumProperty(
        name="Target Group",
        items=[
            ("IRIS", "Iris", ""),
            ("BROW", "Brow", ""),
        ],
        default="IRIS",
    )

    def execute(self, context):
        settings = context.scene.endfield_toon_settings
        if self.target_group == "BROW":
            settings.face_brow_materials.add()
            self.report({"INFO"}, "已添加眉睫材质槽")
        else:
            settings.face_iris_materials.add()
            self.report({"INFO"}, "已添加瞳孔材质槽")
        return {"FINISHED"}


class ENDFIELD_OT_RemoveFaceEyeMaterialSlot(Operator):
    bl_idname = "endfield_toon.remove_face_eye_material_slot"
    bl_label = "移除眼透材质"
    bl_description = "移除一个脸眼一体模式的眼透材质槽"
    bl_options = {"REGISTER", "UNDO"}

    index: IntProperty(name="Index", default=-1, min=-1)
    target_group: EnumProperty(
        name="Target Group",
        items=[
            ("IRIS", "Iris", ""),
            ("BROW", "Brow", ""),
        ],
        default="IRIS",
    )

    def execute(self, context):
        settings = context.scene.endfield_toon_settings
        collection = settings.face_brow_materials if self.target_group == "BROW" else settings.face_iris_materials
        if 0 <= self.index < len(collection):
            collection.remove(self.index)
            self.report({"INFO"}, "已移除眼透材质槽")
            return {"FINISHED"}
        self.report({"WARNING"}, "没有可移除的眼透材质槽")
        return {"CANCELLED"}


class ENDFIELD_OT_AdjustFaceMapping(Operator):
    bl_idname = "endfield_toon.adjust_face_mapping"
    bl_label = "微调脸部贴图映射"
    bl_description = "按固定步长微调脸部 SDF/亮斑贴图的映射"
    bl_options = {"REGISTER", "UNDO"}

    target: EnumProperty(
        name="Target",
        items=[
            ("SDF", "SDF", ""),
            ("CM", "CM", ""),
        ],
    )
    socket_name: EnumProperty(
        name="Socket",
        items=[
            ("Location", "Location", ""),
            ("Scale", "Scale", ""),
        ],
    )
    axis: IntProperty(name="Axis", default=0, min=0, max=2)
    delta: FloatProperty(name="Delta", default=0.0)

    @classmethod
    def poll(cls, context):
        obj = context.object
        return bool(obj and obj.active_material)

    def execute(self, context):
        material = context.object.active_material if context.object else None
        mapping_node = _adjust_face_mapping(material, self.target, self.socket_name, self.axis, self.delta)
        if mapping_node is None:
            self.report({"WARNING"}, "当前材质没有可调的脸部贴图映射")
            return {"CANCELLED"}
        return {"FINISHED"}


class ENDFIELD_OT_OneClickGenerate(Operator):
    bl_idname = "endfield_toon.one_click_generate"
    bl_label = "一键生成"
    bl_description = "替换材质、Alpha、描边与终末地几何节点"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == "MESH"

    def execute(self, context):
        settings = context.scene.endfield_toon_settings
        if settings.apply_selected_objects:
            objects = [obj for obj in context.selected_objects if obj.type == "MESH"]
        else:
            objects = [context.active_object] if context.active_object and context.active_object.type == "MESH" else []

        if not objects:
            self.report({"WARNING"}, "没有可用网格对象")
            return {"CANCELLED"}

        autofilled = 0
        if settings.auto_fill_missing_maps and settings.tex_d:
            autofilled = _autofill_missing_texture_paths(settings)

        library = _effective_library_path(settings)
        if not library:
            self.report({"WARNING"}, "未找到终末地预设库，请先指定 .blend 预设")
            return {"CANCELLED"}

        face_validation_error = _validate_face_helper_targets(settings, objects)
        if face_validation_error:
            self.report({"WARNING"}, face_validation_error)
            return {"CANCELLED"}

        _prime_preset_resources(settings)

        processed = 0
        replaced = 0
        geo_warning = False
        fallback_warning = False
        missing_shadow_maps = False

        if settings.migrate_source_environment:
            _migrate_scene_environment(settings, context.scene)
        if settings.shader_type == "FACE" and (settings.create_helper_rig or settings.auto_geometry_nodes):
            _ensure_sun_rig(settings)

        for obj in objects:
            if settings.clear_custom_normals:
                _clear_custom_split_normals(context, obj)
            _set_shade_smooth(obj)
            _ensure_required_geometry_attributes(obj, settings.shader_type)

            slot_indices = _slot_indices_for_object(obj, settings)
            primary_material = None
            latest_loaded_images = {}
            source_material_map = {}

            for slot_index in slot_indices:
                while slot_index >= len(obj.material_slots):
                    obj.data.materials.append(None)

                source_material = obj.material_slots[slot_index].material
                source_material_key = source_material.as_pointer() if source_material is not None else None
                material_shader_type = _shader_type_for_object(settings, obj, source_material)
                template_material = _ensure_template_material(
                    settings,
                    shader_type=material_shader_type,
                    obj=obj,
                    source_material=source_material,
                )
                fallback_warning = fallback_warning or template_material.name.startswith("ENDFIELD_")
                new_material = template_material.copy()
                new_material.name = f"{template_material.name}_{obj.name}_{slot_index}"
                if settings.shader_type == "FACE" and settings.face_integrated_eye_transparency and material_shader_type in {"PUPIL", "BROW"}:
                    loaded_images, role_presence = _apply_source_material_images(new_material, source_material, material_shader_type)
                else:
                    loaded_images, role_presence = _apply_textures(new_material, settings, shader_type=material_shader_type)
                if template_material.get(SOURCE_LIBRARY_STAMP_KEY):
                    new_material[SOURCE_LIBRARY_STAMP_KEY] = template_material.get(SOURCE_LIBRARY_STAMP_KEY)
                _sync_material_alpha_settings(new_material, template_material)
                if material_shader_type == "FACE":
                    _ensure_face_sdf_mapping_controls(new_material)
                    _ensure_face_cm_mapping_controls(new_material)
                obj.material_slots[slot_index].material = new_material
                if source_material_key is not None:
                    source_material_map.setdefault(source_material_key, []).append(new_material)

                if settings.shader_type == "FACE":
                    if material_shader_type == "FACE" or primary_material is None:
                        primary_material = new_material
                        latest_loaded_images = loaded_images
                else:
                    latest_loaded_images = loaded_images
                    primary_material = primary_material or new_material
                replaced += 1

                if material_shader_type in {"BODY", "CLOTH", "HAIR"}:
                    if (not role_presence.get("tex_n", False)) and (not role_presence.get("tex_p", False)):
                        missing_shadow_maps = True

            outline_material = None
            if settings.shader_type != "PUPIL":
                outline_material = _ensure_outline_material_instance(settings, obj, primary_material, latest_loaded_images)
                if settings.shader_type == "HAIR":
                    _ensure_hair_auxiliary_slots(obj, settings, outline_material)
                else:
                    _ensure_second_outline_slot(obj, outline_material, settings.force_slot2_outline)
            if settings.auto_geometry_nodes and settings.shader_type in {"FACE", "BODY", "CLOTH", "HAIR", "PUPIL"}:
                _remove_solidify_outline_modifiers(obj)
            elif settings.shader_type != "PUPIL":
                _ensure_outline_modifier(obj, settings)

            if settings.auto_geometry_nodes and primary_material is not None:
                geo_warning = _configure_common_geo_modifier(obj, library) or geo_warning

                if settings.shader_type == "FACE":
                    helper_rig = _ensure_head_helper_rig(settings, obj)
                    geo_warning = (
                        _configure_face_modifiers(
                            settings,
                            obj,
                            primary_material,
                            outline_material,
                            helper_rig,
                            library,
                            latest_loaded_images,
                            source_material_map,
                        )
                        or geo_warning
                    )
                elif settings.shader_type == "PUPIL":
                    geo_warning = _configure_eye_object_modifiers(
                        settings,
                        obj,
                        primary_material,
                        library,
                    ) or geo_warning
                elif settings.shader_type == "HAIR":
                    geo_warning = _configure_hair_modifiers(settings, obj, library) or geo_warning
                elif settings.shader_type == "BODY":
                    geo_warning = _configure_surface_outline_modifiers(
                        settings,
                        obj,
                        primary_material,
                        outline_material,
                        library,
                        latest_loaded_images,
                        include_time=True,
                    ) or geo_warning
                elif settings.shader_type == "CLOTH":
                    geo_warning = _configure_surface_outline_modifiers(
                        settings,
                        obj,
                        primary_material,
                        outline_material,
                        library,
                        latest_loaded_images,
                        include_time=True,
                    ) or geo_warning

            processed += 1

        if geo_warning:
            self.report({"WARNING"}, "部分几何节点组未找到，已跳过对应挂载")
        if fallback_warning:
            self.report({"WARNING"}, "部分预设材质未找到，已改用简化备用材质")
        if missing_shadow_maps:
            self.report({"WARNING"}, "缺少 _N/_P 贴图，阴影层次可能不足")

        _cleanup_unused_source_assets(library)
        self.report({"INFO"}, f"完成：{processed} 个网格，替换 {replaced} 个材质槽，自动补图 {autofilled} 个")
        return {"FINISHED"}


def _draw_face_mapping_row(layout, target: str, mapping_node, socket_name: str, index: int, label: str, delta: float):
    if mapping_node is None:
        return
    row = layout.row(align=True)
    minus = row.operator("endfield_toon.adjust_face_mapping", text="-")
    minus.target = target
    minus.socket_name = socket_name
    minus.axis = index
    minus.delta = -delta
    row.prop(mapping_node.inputs[socket_name], "default_value", index=index, text=label)
    plus = row.operator("endfield_toon.adjust_face_mapping", text="+")
    plus.target = target
    plus.socket_name = socket_name
    plus.axis = index
    plus.delta = delta


class ENDFIELD_PT_MainPanel(Panel):
    bl_label = "终末地卡渲材质转换"
    bl_idname = "ENDFIELD_PT_MAIN_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "终末地卡渲"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.endfield_toon_settings

        header = layout.box()
        header.label(text=f"插件版本: {'.'.join(str(v) for v in bl_info['version'])}", icon="INFO")
        header.prop(settings, "preset_library_path")
        library = _effective_library_path(settings)
        if library:
            header.label(text=f"当前预设: {os.path.basename(library)}", icon="CHECKMARK")
        else:
            header.label(text="未检测到终末地预设库", icon="ERROR")
        header.prop(settings, "shader_type")

        tex = layout.box()
        tex.label(text="贴图选择框（动态）")
        for slot in TEXTURE_SLOT_LAYOUT[settings.shader_type]:
            tex.prop(settings, slot.prop_id, text=slot.label)
        tex.operator("endfield_toon.autofill_textures", icon="FILE_REFRESH")

        convert = layout.box()
        convert.label(text="一键生成")
        convert.prop(settings, "apply_selected_objects")
        convert.prop(settings, "apply_mode")
        convert.prop(settings, "auto_fill_missing_maps")
        convert.prop(settings, "clear_custom_normals")
        convert.prop(settings, "migrate_source_environment")
        convert.prop(settings, "auto_geometry_nodes")
        if settings.shader_type == "FACE":
            convert.prop(settings, "create_helper_rig")
            head_box = convert.box()
            head_box.label(text="头部骨骼")
            head_box.prop(settings, "head_bone_armature", text="骨架")
            if settings.head_bone_armature and settings.head_bone_armature.type == "ARMATURE":
                head_box.prop_search(settings, "head_bone_name", settings.head_bone_armature.data, "bones", text="头部骨骼")
            else:
                head_box.prop(settings, "head_bone_name", text="头部骨骼")
                head_box.label(text="留空时自动识别常见 Head 骨骼", icon="INFO")
                head_box.label(text="自动识别失败将中止生成", icon="ERROR")
            convert.prop(settings, "face_integrated_eye_transparency")
            if settings.face_integrated_eye_transparency:
                face_eye_box = layout.box()
                face_eye_box.label(text="脸眼一体眼透材质")
                face_eye_box.label(text="这里只用于指定要处理的材质，并提取原始贴图", icon="INFO")
                face_eye_box.label(text="具体节点结构仍使用当前预设库中的瞳孔/眉睫材质", icon="INFO")
                face_eye_box.label(text="启用后会默认准备 2 个瞳孔槽 + 1 个眉睫槽", icon="INFO")

                iris_box = face_eye_box.box()
                iris_box.label(text="瞳孔栏")
                for index, item in enumerate(settings.face_iris_materials):
                    row = iris_box.row(align=True)
                    row.prop(item, "source_material", text=f"瞳孔材质 {index + 1}")
                    remove_op = row.operator("endfield_toon.remove_face_eye_material_slot", text="", icon="X")
                    remove_op.index = index
                    remove_op.target_group = "IRIS"
                add_iris = iris_box.operator("endfield_toon.add_face_eye_material_slot", icon="ADD")
                add_iris.target_group = "IRIS"

                brow_box = face_eye_box.box()
                brow_box.label(text="眉睫栏")
                for index, item in enumerate(settings.face_brow_materials):
                    row = brow_box.row(align=True)
                    row.prop(item, "source_material", text=f"眉睫材质 {index + 1}")
                    remove_op = row.operator("endfield_toon.remove_face_eye_material_slot", text="", icon="X")
                    remove_op.index = index
                    remove_op.target_group = "BROW"
                add_brow = brow_box.operator("endfield_toon.add_face_eye_material_slot", icon="ADD")
                add_brow.target_group = "BROW"
            else:
                convert.label(text="脸部模式默认不挂载眼透位移", icon="INFO")
        elif settings.shader_type == "PUPIL":
            convert.label(text="眼部模式会将眼透位移挂到当前对象", icon="INFO")
        convert.label(text="建议至少提供 _D + _N/_P 以获得稳定阴影", icon="INFO")

        if settings.shader_type != "PUPIL":
            outline = layout.box()
            outline.label(text="描边系统")
            outline.prop(settings, "force_slot2_outline")
            outline.prop(settings, "outline_thickness")
            outline.prop(settings, "outline_material_offset")
            outline.prop(settings, "outline_modifier_name")

            test_box = layout.box()
            test_box.label(text="优化断边（对当前选中网格）")
            test_box.prop(settings, "test_weld_distance")
            test_box.operator("endfield_toon.test_outline_weld", icon="AUTOMERGE_OFF")
            test_box.separator()
            test_box.operator("endfield_toon.test_outline_proxy", icon="DUPLICATE")
            test_box.separator()
            test_box.prop(settings, "test_gn_merge_distance")
            test_box.operator("endfield_toon.test_outline_gn_merge", icon="GEOMETRY_NODES")
        else:
            eye_box = layout.box()
            eye_box.label(text="眼部模式")
            eye_box.label(text="仅挂载眼透位移，不创建描边", icon="INFO")

        tweak = layout.box()
        tweak.label(text="精细调节（主要参数已隐藏）")
        active_material = context.object.active_material if context.object else None
        shader_node = _find_main_shader_node(active_material)
        shader_type = _detect_shader_type_from_material(active_material)

        if shader_node and shader_type in SAFE_TWEAKS:
            for label, socket_name in SAFE_TWEAKS[shader_type]:
                socket = shader_node.inputs.get(socket_name)
                if socket and hasattr(socket, "default_value"):
                    tweak.prop(socket, "default_value", text=label)
            if shader_type == "FACE":
                mapping_node = _ensure_face_sdf_mapping_controls(active_material)
                if mapping_node:
                    tweak.separator()
                    tweak.label(text="SDF贴图校准")
                    tweak.prop(mapping_node.inputs["Location"], "default_value", index=0, text="SDF位置 X")
                    tweak.prop(mapping_node.inputs["Location"], "default_value", index=1, text="SDF位置 Y")
                    tweak.prop(mapping_node.inputs["Scale"], "default_value", index=0, text="SDF尺寸 X")
                    tweak.prop(mapping_node.inputs["Scale"], "default_value", index=1, text="SDF尺寸 Y")
            if shader_type == "FACE":
                mapping_node = _ensure_face_sdf_mapping_controls(active_material)
                cm_mapping_node = _ensure_face_cm_mapping_controls(active_material)
                if mapping_node:
                    tweak.separator()
                    tweak.label(text="SDF微调按钮")
                    _draw_face_mapping_row(tweak, "SDF", mapping_node, "Location", 0, "SDF X (±0.02)", 0.02)
                    _draw_face_mapping_row(tweak, "SDF", mapping_node, "Location", 1, "SDF Y (±0.02)", 0.02)
                    _draw_face_mapping_row(tweak, "SDF", mapping_node, "Scale", 0, "SDF Scale X (±0.02)", 0.02)
                    _draw_face_mapping_row(tweak, "SDF", mapping_node, "Scale", 1, "SDF Scale Y (±0.02)", 0.02)
                if cm_mapping_node:
                    tweak.separator()
                    tweak.label(text="亮斑贴图微调")
                    _draw_face_mapping_row(tweak, "CM", cm_mapping_node, "Location", 0, "亮斑 X (±0.02)", 0.02)
                    _draw_face_mapping_row(tweak, "CM", cm_mapping_node, "Location", 1, "亮斑 Y (±0.02)", 0.02)
                    _draw_face_mapping_row(tweak, "CM", cm_mapping_node, "Scale", 0, "亮斑 Scale X (±0.02)", 0.02)
                    _draw_face_mapping_row(tweak, "CM", cm_mapping_node, "Scale", 1, "亮斑 Scale Y (±0.02)", 0.02)
        elif shader_type == "BROW":
            tweak.label(text="当前眉毛材质无需额外暴露调节项", icon="INFO")
        else:
            tweak.label(text="先套用终末地材质后，这里会显示安全调节项", icon="INFO")

        credits = layout.box()
        credits.label(text="致谢", icon="HEART")
        credits.label(text="感谢新杨XIYAG大佬制作的仿《明日方舟：终末地》渲染节点")
        credits.label(text="感谢茶叶味香皂大佬配布的《明日方舟：终末地》陈千语")

        layout.operator("endfield_toon.one_click_generate", icon="MATERIAL")


classes = (
    ENDFIELD_PG_FaceEyeMaterialSlot,
    ENDFIELD_PG_Settings,
    ENDFIELD_OT_AutoFillTextures,
    ENDFIELD_OT_TestOutlineWeld,
    ENDFIELD_OT_TestOutlineProxy,
    ENDFIELD_OT_TestOutlineGNMerge,
    ENDFIELD_OT_AddFaceEyeMaterialSlot,
    ENDFIELD_OT_RemoveFaceEyeMaterialSlot,
    ENDFIELD_OT_AdjustFaceMapping,
    ENDFIELD_OT_OneClickGenerate,
    ENDFIELD_PT_MainPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.endfield_toon_settings = PointerProperty(type=ENDFIELD_PG_Settings)
    _endfield_load_post()
    if _endfield_load_post not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_endfield_load_post)


def unregister():
    if _endfield_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_endfield_load_post)
    if hasattr(bpy.types.Scene, "endfield_toon_settings"):
        del bpy.types.Scene.endfield_toon_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

