#!/usr/local/autopkg/python
#
# Copyright 2026 Graham Pugh
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from autopkglib import (  # pylint: disable=import-error
    Processor,
    ProcessorError,
    log_err,
)

try:
    from Foundation import NSPredicate
except ImportError:
    log_err("WARNING: Failed 'from Foundation import NSPredicate' in " + __name__)

__all__ = ["ConditionalVariableAssigner"]


class ConditionalVariableAssigner(Processor):
    """Assigns a value to an environment variable based on an NSPredicate
    condition. If the predicate evaluates to true, the variable named by
    conditional_key is set to value_if_true; otherwise it is set to
    value_if_false.

    The predicate uses NSPredicate syntax, evaluated against the AutoPkg
    environment dictionary. See
    http://developer.apple.com/library/mac/#documentation/Cocoa/Conceptual/Predicates/Articles/pSyntax.html

    Example usage in a recipe:
        - Processor: com.github.grahampugh.recipes/ConditionalVariableAssigner
          Arguments:
            predicate: "os_version BEGINSWITH '15'"
            conditional_key: "MIN_OS_VERSION"
            value_if_true: "15.0"
            value_if_false: "14.0"
    """

    input_variables = {
        "predicate": {
            "required": True,
            "description": (
                "NSPredicate-style comparison against the environment "
                "dictionary. See "
                "http://developer.apple.com/library/mac/#documentation/"
                "Cocoa/Conceptual/Predicates/Articles/pSyntax.html"
            ),
        },
        "conditional_key": {
            "required": True,
            "description": (
                "Name of the environment variable to assign the result to."
            ),
        },
        "value_if_true": {
            "required": True,
            "description": (
                "Value to assign to conditional_key when the predicate "
                "evaluates to true."
            ),
        },
        "value_if_false": {
            "required": True,
            "description": (
                "Value to assign to conditional_key when the predicate "
                "evaluates to false."
            ),
        },
    }
    output_variables = {
        "conditional_key": {
            "description": ("Name of the environment variable that was assigned."),
        },
        "conditional_value": {
            "description": (
                "The value that was assigned to the conditional_key variable."
            ),
        },
    }

    description = __doc__

    def predicate_evaluates_as_true(self, predicate_string):
        """Evaluates predicate against our environment dictionary."""
        try:
            predicate = NSPredicate.predicateWithFormat_(predicate_string)
        except (ValueError, TypeError) as err:
            raise ProcessorError(
                f"Predicate error for '{predicate_string}': {err}"
            ) from err
        result = predicate.evaluateWithObject_(self.env)
        self.output(f"({predicate_string}) is {result}")
        return result

    def main(self):
        """Main process."""
        predicate_string = self.env["predicate"]
        conditional_key = self.env["conditional_key"]
        value_if_true = self.env["value_if_true"]
        value_if_false = self.env["value_if_false"]

        if self.predicate_evaluates_as_true(predicate_string):
            value = value_if_true
        else:
            value = value_if_false

        self.env[conditional_key] = value
        self.env["conditional_value"] = value
        self.output(f"Assigned {conditional_key} = {value}")


if __name__ == "__main__":
    PROCESSOR = ConditionalVariableAssigner()
    PROCESSOR.execute_shell()
