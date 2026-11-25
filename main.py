"""Execute este arquivo para iniciar a interface do programa."""
from pathlib import Path
from views.app_gui import AppContas

if __name__ == '__main__':
    pasta = Path(__file__).resolve().parent
    AppContas(caminho=str(pasta / 'contas.txt')).mainloop()
