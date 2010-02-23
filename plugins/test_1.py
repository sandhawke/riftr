
import plugin

class Red (plugin.Plugin):
    "Red..."
    id = "red"
class Blue (plugin.Plugin):
    "The color of my true love's eyes"
    id = "blue"
class Green (plugin.Plugin):
    "Green..."
    id = "green"

class P (plugin.InputPlugin) :
    """This is test plugin 1"""

    id = "test_1"
    
    options = [
        plugin.Option('option_1', 'Option 1', metavar="X", default=100),
        plugin.Option('color', 'The Color Option', default=Blue.id,
                      values=[Red, Blue, Green], maxcard=None)
        ]

    def __init__(self, **kwargs):
        print "test_1 instantiated with", repr(kwargs)

