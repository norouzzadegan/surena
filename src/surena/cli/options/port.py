import click


class Port(click.ParamType):
    name = "port"

    def __init__(self) -> None:
        super().__init__()

    def convert(self, value, param, ctx):
        def validate_port(port: str) -> bool:
            if int(port) > 65535 or int(port) < 1:
                return False
            return True

        if not validate_port(value):
            self.fail(f'Port "{value}" is not a valid Port.')
        else:
            return value
