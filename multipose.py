import os
import socket
import threading
import re
import atexit
from math import pi
import requests
bl_info = {
    "name": "Multipose Blender Plugin",
    "blender": (2, 80, 0),
    "category": "Import-Export",
}

import bpy

x = []

HOST = '0.0.0.0'
PORT = 65432
_is_running = True
basepath = "./mocAPP_cache_blender/"
model_path = "./models"

char = [
    ("empty", "Only Skeleton", ""),
    ("woman.fbx", "Woman (CC 4.0, Denys Almaral)", ""),
    ("man.fbx", "Man (CC 4.0, Denys Almaral)", ""),
    ("trump.fbx", "Donald Trump (CC 4.0, Denys Almaral)", ""),
    ("doctor.fbx", "Doctor Male (CC 4.0, Denys Almaral)", ""),
    ("police.fbx", "Police Female (CC 4.0, Denys Almaral)", "")
]

def get_files():
    try:
        return os.listdir(basepath)
    except Exception as e:
        return []


def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)


def get_files_list(scene, context):
    return [(val, val, "", idx) for idx, val in enumerate(get_files())]


def get_url_for_name(name):
    return


class ImportLastBVHOperator(bpy.types.Operator):
    """Imports last BVH File sent by MocAPP"""
    bl_idname = "object.import_last_bvh"
    bl_label = "Multipose - Load recorded character"


    recording = bpy.props.EnumProperty(items=get_files_list, name="Recorded Animation", description="Choose your animation that should be loaded.")
    clear_scene = bpy.props.BoolProperty(name="Clear scene", description="Warning! Clears all elements in scene.",  default=True)

    character = bpy.props.EnumProperty(items=char, name="Character", description="Leave empty if you only need the bare skeleton", default="woman.fbx")

    setup_light = bpy.props.BoolProperty(name="Setup light", default=True)
    setup_camera = bpy.props.BoolProperty(name="Setup camera", default=True)

    adjust_to = bpy.props.BoolProperty(name="Update scene fps", default=True)
    update_scene_length = bpy.props.BoolProperty(name="Update scene length", default=True)

    use_cycles = bpy.props.BoolProperty(name="Use Cycles Render System (RECOMMENDED)", default=True)

    def invoke(self, context, event):
        if len(get_files()) == 0:
            ShowMessageBox(message="No files - Send some files to blender via mocAPP!", title="No motion capturing files")
            return {'FINISHED'}
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        # delete scene (if necessary)
        if self.clear_scene:
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete(use_global=False)
        # build scene
        if self.setup_light:
            bpy.ops.object.light_add(type='POINT', location=(-2, 2, 1.8))
            bpy.context.selected_objects[0].name = "Fill Light"
            bpy.context.selected_objects[0].data.name = "Fill Light"

            # set energy
            bpy.context.selected_objects[0].data.energy = 100
            bpy.ops.object.light_add(type='POINT', location=(2, 2, 1.8))
            bpy.context.selected_objects[0].name = "Key Light"
            bpy.context.selected_objects[0].data.name = "Key Light"
            bpy.context.selected_objects[0].data.energy = 200

            bpy.ops.object.light_add(type='POINT', location=(2, -2, 1.8), radius=4.0)
            bpy.context.selected_objects[0].name = "Back Light"
            bpy.context.selected_objects[0].data.name = "Back Light"
            bpy.context.selected_objects[0].data.energy = 70
            # make it softer
            bpy.context.selected_objects[0].data.shadow_soft_size = 3.0
        if self.setup_camera:
            bpy.ops.object.camera_add(enter_editmode=False, align='WORLD', location=(0, 7, 2), rotation=(pi*6/13 , 0, pi))
        print("-----")
        print(self.recording)
        print("-----")
        bpy.ops.import_anim.bvh(filepath=basepath + self.recording, update_scene_fps=self.adjust_to, update_scene_duration=self.update_scene_length)
        # scale down
        bpy.ops.transform.resize(value=(.1, .1, .1))
        skel = bpy.context.selected_objects[0]
        print(skel)
        if self.character != "empty":
            # put the character into rest position
            bpy.context.object.data.pose_position = 'REST'
            bpy.ops.import_scene.fbx( filepath = os.path.join(model_path, self.character))
            model = bpy.context.selected_objects[0]
            model.select_set(True)
            skel.select_set(True)
            bpy.context.view_layer.objects.active = skel
            bpy.ops.object.parent_set(type="ARMATURE_AUTO")
            bpy.context.object.data.pose_position = 'POSE'
        bpy.context.scene.render.engine = 'CYCLES'
        ShowMessageBox(message="Imported character %s" % self.recording, title="Success!")
        return {'FINISHED'}


class MessageBoxOperator(bpy.types.Operator):
    bl_idname = "ui.show_message_box"
    bl_label = "Minimal Operator"

    def execute(self, context):
        #this is where I send the message
        self.report({'INFO'}, "This is a test")
        return {'FINISHED'}


def menu_function(self, context):
    self.layout.operator(ImportLastBVHOperator.bl_idname)


def register():
    bpy.utils.register_class(ImportLastBVHOperator)
    bpy.utils.register_class(MessageBoxOperator)
    bpy.types.VIEW3D_MT_object.append(menu_function)


def unregister():
    bpy.utils.unregister_class(ImportLastBVHOperator)
    bpy.utils.unregister_class(MessageBoxOperator)



def get_unique_name(original_name):
    short_form = original_name.split(".bvh")[0]
    new_name = short_form
    i = 1
    print(x)
    while(next((True for ob in get_files() if ob.split(".bvh")[0] == new_name), False)):
        print("Name exists already")
        new_name = short_form + " v%d" % i
        i+=1
    return new_name + ".bvh"


def get_bvh(url, token):
    r = requests.get(url)
    d = r.headers['content-disposition']
    fname = get_unique_name(re.findall("filename=(.+)", d)[0].replace('"', ''))
    print(fname)
    fpath = os.path.join(basepath, fname)
    #x.append({"path":fpath, "name":get_unique_name(fname)})
    if not os.path.exists(basepath):
        os.makedirs(basepath)
    try:
        open(fpath, 'wb').write(r.content)
    except FileExistsError as e:
        print(e)
        pass


def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print("Starting a server on", HOST, PORT)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        while _is_running:
            conn, addr = s.accept()
            with conn:
                url = None
                token = None
                conn.send(b'\x00')
                while True:
                    try:
                        data = conn.recv(1024)
                        dc = data.decode()
                        if "url=" and "token=" in dc:
                            url = dc.split("url=")[1].split("\n")[0]
                            token = dc.split("token=")[1].split("\n")[0]
                        if url is not None and token is not None:
                            get_bvh(url, token)
                            url = None
                            token = None
                        if not data:
                            break
                        conn.sendall(data)
                    except ConnectionResetError:
                        break



def stop_server():
    print("Stopping the socket.")
    _is_running = False

# run a server thread.
t = threading.Thread(target=run_server)
t.daemon = True
t.start()

atexit.register(stop_server)
