from core.login import Login
from core.ticket import Ticket


def main():
    Login().login()
    Ticket().check()


if __name__ == '__main__':
    while True:
        main()
