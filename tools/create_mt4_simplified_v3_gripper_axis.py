from pathlib import Path
import shutil

try:
    from isaacsim import SimulationApp
except Exception:
    from omni.isaac.kit import SimulationApp

simulation_app = SimulationApp({"headless": True})

from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics

try:
    from pxr import PhysxSchema
except Exception:
    PhysxSchema = None


PROJECT_DIR = Path.home() / "work/robotarm/mt4_isaac_lab_task"
SRC = PROJECT_DIR / "assets/usd/mt4_simplified_v2.usd"
DST = PROJECT_DIR / "assets/usd/mt4_simplified_v3.usd"
ROOT = "/mt4_simplified_v2"


def set_attr(prim, name, type_name, value):
    attr = prim.GetAttribute(name)
    if not attr:
        attr = prim.CreateAttribute(name, type_name)
    attr.Set(value)


def main():
    if not SRC.exists():
        raise SystemExit(f"[ERROR] source USD not found: {SRC}")

    shutil.copy2(SRC, DST)
    stage = Usd.Stage.Open(str(DST))
    if stage is None:
        raise SystemExit(f"[ERROR] could not open copied USD: {DST}")

    root = stage.GetPrimAtPath(ROOT)
    if not root:
        raise SystemExit(f"[ERROR] root prim not found: {ROOT}")

    gripper = UsdGeom.Xform.Define(stage, f"{ROOT}/gripper_link")
    gripper_prim = gripper.GetPrim()
    gripper.ClearXformOpOrder()
    gripper.AddTranslateOp().Set(Gf.Vec3f(0.38, 0.0, 0.09))
    gripper.AddOrientOp().Set(Gf.Quatf(1.0, 0.0, 0.0, 0.0))
    gripper.AddScaleOp().Set(Gf.Vec3f(1.0, 1.0, 1.0))

    UsdPhysics.RigidBodyAPI.Apply(gripper_prim)
    UsdPhysics.MassAPI.Apply(gripper_prim)
    set_attr(gripper_prim, "physics:rigidBodyEnabled", Sdf.ValueTypeNames.Bool, True)
    set_attr(gripper_prim, "physics:kinematicEnabled", Sdf.ValueTypeNames.Bool, False)
    set_attr(gripper_prim, "physics:mass", Sdf.ValueTypeNames.Float, 0.12)
    set_attr(gripper_prim, "physics:centerOfMass", Sdf.ValueTypeNames.Point3f, Gf.Vec3f(0.08, 0.0, 0.0))
    set_attr(gripper_prim, "physics:diagonalInertia", Sdf.ValueTypeNames.Vector3f, Gf.Vec3f(0.0004, 0.0006, 0.0006))
    set_attr(gripper_prim, "physics:principalAxes", Sdf.ValueTypeNames.Quatf, Gf.Quatf(1.0, 0.0, 0.0, 0.0))

    visuals = UsdGeom.Xform.Define(stage, f"{ROOT}/gripper_link/visuals")
    collisions = UsdGeom.Xform.Define(stage, f"{ROOT}/gripper_link/collisions")
    visuals.GetPrim().CreateAttribute("purpose", Sdf.ValueTypeNames.Token).Set("default")
    collisions.GetPrim().CreateAttribute("purpose", Sdf.ValueTypeNames.Token).Set("guide")
    collisions.GetPrim().CreateAttribute("visibility", Sdf.ValueTypeNames.Token).Set("invisible")

    # Match the existing MT4 link convention: each child link starts at its
    # parent joint and extends along local +X.
    hinge = UsdGeom.Cylinder.Define(stage, f"{ROOT}/gripper_link/visuals/pitch_hinge")
    hinge.CreateRadiusAttr(0.028)
    hinge.CreateHeightAttr(0.075)
    hinge.CreateAxisAttr("Y")
    hinge.ClearXformOpOrder()
    hinge.AddTranslateOp().Set(Gf.Vec3f(0.0, 0.0, 0.0))
    hinge.CreateDisplayColorAttr([Gf.Vec3f(0.18, 0.18, 0.18)])

    visual_parts = {
        "mount_arm": ((0.055, 0.0, 0.0), (0.055, 0.016, 0.016), (0.12, 0.12, 0.12)),
        "tool_mount": ((0.125, 0.0, 0.0), (0.025, 0.032, 0.024), (0.09, 0.09, 0.09)),
        "left_finger": ((0.185, 0.034, 0.0), (0.055, 0.009, 0.010), (0.02, 0.02, 0.02)),
        "right_finger": ((0.185, -0.034, 0.0), (0.055, 0.009, 0.010), (0.02, 0.02, 0.02)),
        "left_pad": ((0.238, 0.034, 0.0), (0.012, 0.016, 0.015), (0.00, 0.45, 0.95)),
        "right_pad": ((0.238, -0.034, 0.0), (0.012, 0.016, 0.015), (0.00, 0.45, 0.95)),
        "tip_bridge": ((0.248, 0.0, 0.0), (0.005, 0.022, 0.007), (0.00, 0.18, 0.85)),
    }
    for name, (translate, scale, color) in visual_parts.items():
        cube = UsdGeom.Cube.Define(stage, f"{ROOT}/gripper_link/visuals/{name}")
        cube.CreateSizeAttr(1.0)
        cube.ClearXformOpOrder()
        cube.AddTranslateOp().Set(Gf.Vec3f(*translate))
        cube.AddScaleOp().Set(Gf.Vec3f(*scale))
        cube.CreateDisplayColorAttr([Gf.Vec3f(*color)])

    collision_parts = {
        "hinge": ((0.000, 0.0, 0.0), (0.028, 0.040, 0.028)),
        "mount_arm": ((0.055, 0.0, 0.0), (0.055, 0.016, 0.016)),
        "tool_mount": ((0.125, 0.0, 0.0), (0.025, 0.032, 0.024)),
        "left_finger": ((0.185, 0.034, 0.0), (0.055, 0.009, 0.010)),
        "right_finger": ((0.185, -0.034, 0.0), (0.055, 0.009, 0.010)),
    }
    for name, (translate, scale) in collision_parts.items():
        cube = UsdGeom.Cube.Define(stage, f"{ROOT}/gripper_link/collisions/{name}")
        cube.CreateSizeAttr(1.0)
        cube.ClearXformOpOrder()
        cube.AddTranslateOp().Set(Gf.Vec3f(*translate))
        cube.AddScaleOp().Set(Gf.Vec3f(*scale))
        UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
        set_attr(cube.GetPrim(), "physics:collisionEnabled", Sdf.ValueTypeNames.Bool, True)
        set_attr(cube.GetPrim(), "purpose", Sdf.ValueTypeNames.Token, "guide")
        set_attr(cube.GetPrim(), "visibility", Sdf.ValueTypeNames.Token, "invisible")

    joint = UsdPhysics.RevoluteJoint.Define(stage, f"{ROOT}/joints/gripper_pitch")
    joint_prim = joint.GetPrim()
    UsdPhysics.DriveAPI.Apply(joint_prim, "angular")
    if PhysxSchema is not None:
        PhysxSchema.PhysxJointAPI.Apply(joint_prim)
    joint.CreateBody0Rel().SetTargets([Sdf.Path(f"{ROOT}/wrist_link")])
    joint.CreateBody1Rel().SetTargets([Sdf.Path(f"{ROOT}/gripper_link")])
    joint.CreateAxisAttr("Y")
    joint.CreateLocalPos0Attr(Gf.Vec3f(0.06, 0.0, 0.0))
    joint.CreateLocalPos1Attr(Gf.Vec3f(0.0, 0.0, 0.0))
    joint.CreateLocalRot0Attr(Gf.Quatf(0.0, 1.0, 0.0, 0.0))
    joint.CreateLocalRot1Attr(Gf.Quatf(0.0, 1.0, 0.0, 0.0))
    joint.CreateLowerLimitAttr(-68.75493621826172)
    joint.CreateUpperLimitAttr(68.75493621826172)
    set_attr(joint_prim, "physics:collisionEnabled", Sdf.ValueTypeNames.Bool, False)
    set_attr(joint_prim, "physics:jointEnabled", Sdf.ValueTypeNames.Bool, True)
    set_attr(joint_prim, "drive:angular:physics:targetPosition", Sdf.ValueTypeNames.Float, 0.0)
    set_attr(joint_prim, "drive:angular:physics:stiffness", Sdf.ValueTypeNames.Float, 625.0)
    set_attr(joint_prim, "drive:angular:physics:damping", Sdf.ValueTypeNames.Float, 0.0)
    set_attr(joint_prim, "drive:angular:physics:maxForce", Sdf.ValueTypeNames.Float, 120.0)

    stage.GetRootLayer().Save()
    print(f"[OK] wrote {DST}")


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
