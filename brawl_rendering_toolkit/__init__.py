'''
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

bl_info = {
    "name": "Brawl Rendering Toolkit",
    "author": "tryptech, Wayde Brandon Moss",
    "version": (1, 3, 10),
    "blender": (2, 81, 0),
    "location": "View3D > Sidebar > Tool",
    "description": "Super Smash Bros. Brawl Rendering Tools and Shortcuts",
    "category": "3D View"}

import bpy, traceback

def register():

    from . import modules
    from . import operators
    from . import props
    from . import ui

    from .bpy_class import classes

    for cls in classes:
        bpy.utils.register_class(cls)

    props.renderProps.register()

    
def unregister():

    from . import modules
    from . import operators
    from . import props
    from . import ui

    from .bpy_class import classes
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError as e:
            print(f'Failed to unregister brawl_rendering_toolkit; Error="{e}" ; Traceback=\n{traceback.format_exc()}')


if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()