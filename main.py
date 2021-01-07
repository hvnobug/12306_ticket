from core.login import Login
from core.ticket import Ticket
from utils import console
from utils.file import read_as_str


def main():
    Login().login()
    Ticket().check()


if __name__ == '__main__':
    console.print(read_as_str('./banner.txt'))
    while True:
        main()
