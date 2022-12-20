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
    "version": (1, 2, 3),
    "blender": (2, 81, 0),
    "location": "View3D > Sidebar > Tool",
    "description": "Super Smash Bros. Brawl Rendering Tools and Shortcuts",
    "category": "3D View"}

import bpy
import traceback

def register():

    from .bpy_class import classes

    for cls in classes:
        bpy.utils.register_class(cls)

    
def unregister():

    from .bpy_class import classes
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError as e:
            print(f'Failed to unregister smash_ultimate_blender; Error="{e}" ; Traceback=\n{traceback.format_exc()}')


if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()