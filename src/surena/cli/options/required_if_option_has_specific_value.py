from typing import Any, List, Mapping, Tuple, Type

import click


def required_if_option_has_specific_value(option_name: str, option_value: str) -> Type[click.Option]:
    option_name = option_name.replace("-", "_")

    class RequiredIfOptionHasSpecificValue(click.Option):
        def __init__(self, *args: Any, **kwargs: Any):
            kwargs["required"] = kwargs.get("required", True)
            super().__init__(*args, **kwargs)

        def handle_parse_result(
            self, context: click.Context, options: Mapping[str, Any], args: List[str]
        ) -> Tuple[Any, List[str]]:
            if option_name not in options:
                raise click.UsageError(
                    f'The option "{option_name}" you entered does not exist in option '
                    f'list "{list(options.keys())}".'
                )

            if option_value != options[option_name]:
                self.required = False
            return super().handle_parse_result(context, options, args)

    return RequiredIfOptionHasSpecificValue
