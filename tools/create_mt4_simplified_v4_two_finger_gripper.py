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
DST = PROJECT_DIR / "assets/usd/mt4_simplified_v4_two_finger.usd"
ROOT = "/mt4_simplified_v2"


def set_attr(prim, name, type_name, value):
    attr = prim.GetAttribute(name)
    if not attr:
        attr = prim.CreateAttribute(name, type_name)
    attr.Set(value)


def add_cube(stage, path, translate, scale, color=None, collision=False):
    cube = UsdGeom.Cube.Define(stage, path)
    cube.CreateSizeAttr(1.0)
    cube.ClearXformOpOrder()
    cube.AddTranslateOp().Set(Gf.Vec3f(*translate))
    cube.AddScaleOp().Set(Gf.Vec3f(*scale))
    if color is not None:
        cube.CreateDisplayColorAttr([Gf.Vec3f(*color)])
    if collision:
        UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
        set_attr(cube.GetPrim(), "physics:collisionEnabled", Sdf.ValueTypeNames.Bool, True)
    return cube


def apply_body(prim, mass, center_of_mass, inertia):
    UsdPhysics.RigidBodyAPI.Apply(prim)
    UsdPhysics.MassAPI.Apply(prim)
    set_attr(prim, "physics:rigidBodyEnabled", Sdf.ValueTypeNames.Bool, True)
    set_attr(prim, "physics:kinematicEnabled", Sdf.ValueTypeNames.Bool, False)
    set_attr(prim, "physics:mass", Sdf.ValueTypeNames.Float, mass)
    set_attr(prim, "physics:centerOfMass", Sdf.ValueTypeNames.Point3f, Gf.Vec3f(*center_of_mass))
    set_attr(prim, "physics:diagonalInertia", Sdf.ValueTypeNames.Vector3f, Gf.Vec3f(*inertia))
    set_attr(prim, "physics:principalAxes", Sdf.ValueTypeNames.Quatf, Gf.Quatf(1.0, 0.0, 0.0, 0.0))


def add_revolute_joint(stage):
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
    set_attr(joint_prim, "drive:angular:physics:damping", Sdf.ValueTypeNames.Float, 35.0)
    set_attr(joint_prim, "drive:angular:physics:maxForce", Sdf.ValueTypeNames.Float, 120.0)


def add_prismatic_joint(stage, name, body_path, local_y, lower, upper, stiffness=1800.0):
    joint = UsdPhysics.PrismaticJoint.Define(stage, f"{ROOT}/joints/{name}")
    joint_prim = joint.GetPrim()
    UsdPhysics.DriveAPI.Apply(joint_prim, "linear")
    if PhysxSchema is not None:
        PhysxSchema.PhysxJointAPI.Apply(joint_prim)
    joint.CreateBody0Rel().SetTargets([Sdf.Path(f"{ROOT}/gripper_link")])
    joint.CreateBody1Rel().SetTargets([Sdf.Path(body_path)])
    joint.CreateAxisAttr("Y")
    joint.CreateLocalPos0Attr(Gf.Vec3f(0.120, local_y, 0.0))
    joint.CreateLocalPos1Attr(Gf.Vec3f(0.0, 0.0, 0.0))
    joint.CreateLowerLimitAttr(lower)
    joint.CreateUpperLimitAttr(upper)
    set_attr(joint_prim, "physics:collisionEnabled", Sdf.ValueTypeNames.Bool, False)
    set_attr(joint_prim, "physics:jointEnabled", Sdf.ValueTypeNames.Bool, True)
    set_attr(joint_prim, "drive:linear:physics:targetPosition", Sdf.ValueTypeNames.Float, 0.0)
    set_attr(joint_prim, "drive:linear:physics:stiffness", Sdf.ValueTypeNames.Float, stiffness)
    set_attr(joint_prim, "drive:linear:physics:damping", Sdf.ValueTypeNames.Float, 80.0)
    set_attr(joint_prim, "drive:linear:physics:maxForce", Sdf.ValueTypeNames.Float, 60.0)


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
    apply_body(gripper_prim, 0.10, (0.055, 0.0, 0.0), (0.00025, 0.00035, 0.00035))

    visuals = UsdGeom.Xform.Define(stage, f"{ROOT}/gripper_link/visuals")
    collisions = UsdGeom.Xform.Define(stage, f"{ROOT}/gripper_link/collisions")
    visuals.GetPrim().CreateAttribute("purpose", Sdf.ValueTypeNames.Token).Set("default")
    collisions.GetPrim().CreateAttribute("purpose", Sdf.ValueTypeNames.Token).Set("guide")
    collisions.GetPrim().CreateAttribute("visibility", Sdf.ValueTypeNames.Token).Set("invisible")

    hinge = UsdGeom.Cylinder.Define(stage, f"{ROOT}/gripper_link/visuals/pitch_hinge")
    hinge.CreateRadiusAttr(0.028)
    hinge.CreateHeightAttr(0.075)
    hinge.CreateAxisAttr("Y")
    hinge.ClearXformOpOrder()
    hinge.AddTranslateOp().Set(Gf.Vec3f(0.0, 0.0, 0.0))
    hinge.CreateDisplayColorAttr([Gf.Vec3f(0.18, 0.18, 0.18)])

    add_cube(stage, f"{ROOT}/gripper_link/visuals/mount_arm", (0.030, 0.0, 0.0), (0.030, 0.016, 0.016), (0.12, 0.12, 0.12))
    add_cube(stage, f"{ROOT}/gripper_link/visuals/tool_mount", (0.072, 0.0, 0.0), (0.018, 0.032, 0.024), (0.09, 0.09, 0.09))
    add_cube(stage, f"{ROOT}/gripper_link/collisions/mount_arm", (0.030, 0.0, 0.0), (0.030, 0.016, 0.016), collision=True)
    add_cube(stage, f"{ROOT}/gripper_link/collisions/tool_mount", (0.072, 0.0, 0.0), (0.018, 0.032, 0.024), collision=True)

    for side, y, color in (
        ("left", 0.034, (0.02, 0.02, 0.02)),
        ("right", -0.034, (0.02, 0.02, 0.02)),
    ):
        finger = UsdGeom.Xform.Define(stage, f"{ROOT}/{side}_finger_link")
        finger_prim = finger.GetPrim()
        finger.ClearXformOpOrder()
        finger.AddTranslateOp().Set(Gf.Vec3f(0.50, y, 0.09))
        finger.AddOrientOp().Set(Gf.Quatf(1.0, 0.0, 0.0, 0.0))
        finger.AddScaleOp().Set(Gf.Vec3f(1.0, 1.0, 1.0))
        apply_body(finger_prim, 0.025, (0.030, 0.0, 0.0), (0.00003, 0.00003, 0.00002))

        f_visuals = UsdGeom.Xform.Define(stage, f"{ROOT}/{side}_finger_link/visuals")
        f_collisions = UsdGeom.Xform.Define(stage, f"{ROOT}/{side}_finger_link/collisions")
        f_collisions.GetPrim().CreateAttribute("purpose", Sdf.ValueTypeNames.Token).Set("guide")
        f_collisions.GetPrim().CreateAttribute("visibility", Sdf.ValueTypeNames.Token).Set("invisible")

        pad_color = (0.0, 0.45, 0.95)
        add_cube(stage, f"{ROOT}/{side}_finger_link/visuals/finger", (0.000, 0.0, 0.0), (0.040, 0.009, 0.010), color)
        add_cube(stage, f"{ROOT}/{side}_finger_link/visuals/pad", (0.038, 0.0, 0.0), (0.010, 0.016, 0.015), pad_color)
        add_cube(stage, f"{ROOT}/{side}_finger_link/collisions/finger", (0.000, 0.0, 0.0), (0.040, 0.009, 0.010), collision=True)
        add_cube(stage, f"{ROOT}/{side}_finger_link/collisions/pad", (0.038, 0.0, 0.0), (0.010, 0.016, 0.015), collision=True)

    add_revolute_joint(stage)
    add_prismatic_joint(stage, "left_finger_slide", f"{ROOT}/left_finger_link", 0.034, -0.018, 0.004)
    add_prismatic_joint(stage, "right_finger_slide", f"{ROOT}/right_finger_link", -0.034, -0.004, 0.018)

    stage.GetRootLayer().Save()
    print(f"[OK] wrote {DST}")


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
