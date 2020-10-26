import os
import socket
import threading
import re
import atexit
import requests
bl_info = {
    "name": "Import BVH over Network",
    "blender": (2, 80, 0),
    "category": "Import-Export",
}

import bpy

x = []


def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)


class ImportLastBVHOperator(bpy.types.Operator):
    """Imports last BVH File sent by MocAPP"""
    bl_idname = "object.import_last_bvh"
    bl_label = "moCAPP - Import last bvh"

    adjust_to = bpy.props.BoolProperty(name="Update scene fps")
    update_scene_length = bpy.props.BoolProperty(name="Update scene length")
    def invoke(self, context, event):
        if len(x) == 0:
            ShowMessageBox(message="No files in this session - Send some files to blender via mocAPP!", title="No motion capturing files")
            return {'FINISHED'}
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        print(x)
        bpy.ops.import_anim.bvh(filepath=x[len(x) - 1], update_scene_fps=self.adjust_to, update_scene_duration=self.update_scene_length)
        return {'FINISHED'}


class MessageBoxOperator(bpy.types.Operator):
    bl_idname = "ui.show_message_box"
    bl_label = "Minimal Operator"

    def execute(self, context):
        #this is where I send the message
        self.report({'INFO'}, "This is a test")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(ImportLastBVHOperator)
    bpy.utils.register_class(MessageBoxOperator)


def unregister():
    bpy.utils.unregister_class(ImportLastBVHOperator)
    bpy.utils.unregister_class(MessageBoxOperator)


HOST = '0.0.0.0'
PORT = 65432
_is_running = True
basepath = "/tmp/mocAPP_cache_blender/"


def get_bvh(url, token):
    # TODO: 1 - get id not url, 2 - offer options to smoothen the file
    r = requests.get(url)
    d = r.headers['content-disposition']
    fname = re.findall("filename=(.+)", d)[0]
    fpath = os.path.join(basepath, fname)
    x.append(fpath)
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

if __name__ == "__main__":
    register()

