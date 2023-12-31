"""Test prompts."""

from unittest.mock import MagicMock

import pytest

from llama_index.bridge.langchain import PromptTemplate
from llama_index.llms.base import LLM
from llama_index.llms.openai import OpenAI
from llama_index.prompts.base import Prompt
from llama_index.prompts.prompt_selector import PromptSelector


def is_openai(llm: LLM) -> bool:
    """Test condition."""
    return isinstance(llm, OpenAI)


def test_partial_format() -> None:
    """Test partial format."""
    prompt_txt = "hello {text} {foo}"
    prompt = Prompt(prompt_txt)

    prompt_fmt = prompt.partial_format(foo="bar")

    assert isinstance(prompt_fmt, Prompt)
    assert prompt_fmt.format(text="world") == "hello world bar"


def test_from_prompt() -> None:
    """Test new prompt from a partially formatted prompt."""
    prompt_txt = "hello {text} {foo}"
    prompt = Prompt(prompt_txt)
    prompt_fmt = prompt.partial_format(foo="bar")

    prompt_new = Prompt.from_prompt(prompt_fmt)
    assert isinstance(prompt_new, Prompt)

    assert prompt_new.format(text="world2") == "hello world2 bar"


def test_from_langchain_prompt() -> None:
    """Test from langchain prompt."""
    prompt_txt = "hello {text} {foo}"
    prompt = PromptTemplate(input_variables=["text", "foo"], template=prompt_txt)
    prompt_new = Prompt.from_langchain_prompt(prompt)

    assert isinstance(prompt_new, Prompt)
    assert prompt_new.prompt == prompt
    assert prompt_new.format(text="world2", foo="bar") == "hello world2 bar"

    # test errors if we specify both template and langchain prompt
    with pytest.raises(ValueError):
        prompt_txt = "hello {text} {foo}"
        prompt = PromptTemplate(input_variables=["text", "foo"], template=prompt_txt)
        Prompt(template=prompt_txt, langchain_prompt=prompt)


def test_from_langchain_prompt_selector() -> None:
    """Test from langchain prompt selector."""
    prompt_txt = "hello {text} {foo}"
    prompt_txt_2 = "world {text} {foo}"
    prompt = PromptTemplate(input_variables=["text", "foo"], template=prompt_txt)
    prompt_2 = PromptTemplate(input_variables=["text", "foo"], template=prompt_txt_2)

    test_prompt_selector = PromptSelector(
        default_prompt=prompt, conditionals=[(is_openai, prompt_2)]
    )

    test_llm = MagicMock(spec=OpenAI)

    prompt_new = Prompt.from_langchain_prompt_selector(test_prompt_selector)
    assert isinstance(prompt_new, Prompt)
    assert prompt_new.prompt == prompt
    assert prompt_new.format(text="world2", foo="bar") == "hello world2 bar"
    assert (
        prompt_new.format(llm=test_llm, text="world2", foo="bar") == "world world2 bar"
    )

    test_lc_prompt = prompt_new.get_langchain_prompt(llm=test_llm)
    assert test_lc_prompt == prompt_2
    test_lc_prompt = prompt_new.get_langchain_prompt(llm=None)
    assert test_lc_prompt == prompt

    # test errors if langchain prompt input var doesn't match
    with pytest.raises(ValueError):
        prompt_txt = "hello {text} {foo}"
        prompt_txt_2 = "world {text} {foo} {tmp}"
        prompt = PromptTemplate(input_variables=["text", "foo"], template=prompt_txt)
        prompt_2 = PromptTemplate(
            input_variables=["text", "foo", "tmp"], template=prompt_txt_2
        )

        test_prompt_selector = PromptSelector(
            prompt=prompt, conditionals=([is_openai], [prompt_2])
        )
        prompt_new = Prompt.from_langchain_prompt_selector(test_prompt_selector)
