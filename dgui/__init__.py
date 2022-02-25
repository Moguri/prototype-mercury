from .commonui import CommonUI
from .title import TitleUI
from .workshop import WorkshopUI
from .combat import CombatUI
from .saveload import SaveUI, LoadUI

UIS = {
    'common': CommonUI,
    'title': TitleUI,
    'workshop': WorkshopUI,
    'combat': CombatUI,
    'save': SaveUI,
    'load': LoadUI,
}
