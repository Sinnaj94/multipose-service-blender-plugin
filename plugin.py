import socket
import threading
bl_info = {
    "name": "Import BVH over Network",
    "blender": (2, 80, 0),
    "category": "Import-Export",
}

import bpy

class StartServer(bpy.types.Operator):
    """Start the mocAPP Server"""      # Use this as a tooltip for menu items and buttons.
    bl_idname = "import.bvh"        # Unique identifier for buttons and menu items to reference.
    bl_label = "Import BVH over Network"         # Display name in the interface.
    bl_options = {'REGISTER'}  # Enable undo for the operator.

    def execute(self, context):        # execute() is called when running the operator.

        # The original script
        bpy.ops.import_anim.bvh(filepath="/home/worker/Downloads/02_02.bvh")

        return {'FINISHED'}            # Lets Blender know the operator finished successfully.

def register():
    bpy.utils.register_class(StartServer)


def unregister():
    bpy.utils.unregister_class(StartServer)


HOST = '127.0.0.1'
PORT = 65432

def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        conn, addr = s.accept()
        with conn:
            print('Connected with ', addr)
            conn.send("Blender 2.80")
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                conn.sendall(data)

# run a server thread.
t = threading.Thread(target=run_server)
t.daemon = True
t.start()

if __name__ == "__main__":
    register()