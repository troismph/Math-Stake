from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class GeneratedProblem:
    expression: str
    answer: int


def has_carry(left: int, right: int) -> bool:
    left = abs(left)
    right = abs(right)
    while left or right:
        if left % 10 + right % 10 >= 10:
            return True
        left //= 10
        right //= 10
    return False


def has_borrow(left: int, right: int) -> bool:
    left = abs(left)
    right = abs(right)
    borrow = 0
    while left or right:
        current_digit = left % 10 - borrow
        target_digit = right % 10
        if current_digit < target_digit:
            return True
        borrow = 0
        left //= 10
        right //= 10
    return False


def step_has_transfer(left_value: int, operator: str, right_value: int) -> bool:
    if operator == "+":
        if left_value >= 0:
            return has_carry(left_value, right_value)
        return has_borrow(max(abs(left_value), right_value), min(abs(left_value), right_value))

    if left_value >= 0:
        return has_borrow(left_value, right_value)
    return has_carry(abs(left_value), right_value)


def apply_operation(left_value: int, operator: str, right_value: int) -> int:
    if operator == "+":
        return left_value + right_value
    return left_value - right_value


def generate_paper(config, *, rng: random.Random | None = None, max_attempts: int | None = None) -> list[GeneratedProblem]:
    rng = rng or random.Random()
    target_count = config.question_count
    max_attempts = max_attempts or max(200, target_count * 50)

    seen_expressions: set[str] = set()
    problems: list[GeneratedProblem] = []
    for _ in range(max_attempts):
        if len(problems) >= target_count:
            break

        problem = generate_problem(
            number_count=config.number_count,
            max_operand=config.max_operand,
            allow_negative_intermediate=config.allow_negative_intermediate,
            rng=rng,
        )
        if problem is None or problem.expression in seen_expressions:
            continue

        seen_expressions.add(problem.expression)
        problems.append(problem)

    return problems


def generate_problem(*, number_count: int, max_operand: int, allow_negative_intermediate: bool, rng: random.Random) -> GeneratedProblem | None:
    starting_values = list(range(max_operand + 1))
    rng.shuffle(starting_values)

    for starting_value in starting_values:
        built = _build_expression(
            running_total=starting_value,
            remaining_steps=number_count - 1,
            max_operand=max_operand,
            allow_negative_intermediate=allow_negative_intermediate,
            rng=rng,
            tokens=[str(starting_value)],
        )
        if built is None:
            continue

        expression_tokens, answer = built
        return GeneratedProblem(expression=" ".join(expression_tokens), answer=answer)

    return None


def _build_expression(
    *,
    running_total: int,
    remaining_steps: int,
    max_operand: int,
    allow_negative_intermediate: bool,
    rng: random.Random,
    tokens: list[str],
) -> tuple[list[str], int] | None:
    if remaining_steps == 0:
        if running_total < 0:
            return None
        return tokens, running_total

    operators = ["+", "-"]
    operands = list(range(max_operand + 1))
    rng.shuffle(operators)
    rng.shuffle(operands)

    for operator in operators:
        for operand in operands:
            if not step_has_transfer(running_total, operator, operand):
                continue

            next_total = apply_operation(running_total, operator, operand)
            if not allow_negative_intermediate and next_total < 0:
                continue

            max_recovery = (remaining_steps - 1) * max_operand
            if next_total + max_recovery < 0:
                continue

            built = _build_expression(
                running_total=next_total,
                remaining_steps=remaining_steps - 1,
                max_operand=max_operand,
                allow_negative_intermediate=allow_negative_intermediate,
                rng=rng,
                tokens=[*tokens, operator, str(operand)],
            )
            if built is not None:
                return built

    return None