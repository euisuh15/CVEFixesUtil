import requests

# ponytail: vllm imported lazily inside the two functions that need it, so metrics,
# templating and CWE lookup stay usable (and testable) on a machine without a GPU.


def calculate_metrics(df, pred_before, pred_after):
    tp = 0
    fp = 0
    tn = 0
    fn = 0
    na_b = 0
    na_a = 0

    for i in range(df.shape[0]):
        res_before = str(df[pred_before].iloc[i]).lower()
        res_after = str(df[pred_after].iloc[i]).lower()

        if res_before == "1":
            tp += 1
        elif res_before == "0":
            fn += 1
        elif res_before == "-1":
            na_b += 1

        if res_after == "1":
            fp += 1
        elif res_after == "0":
            tn += 1
        elif res_after == "-1":
            na_a += 1

    return tp, fp, tn, fn, na_b, na_a


def template(prompts, systems=None, mode="llama3"):
    if mode == "llama3":
        results = []
        systems = systems or [""] * len(
            prompts
        )  # Default to empty strings if systems is None or shorter than prompts

        for i, prompt in enumerate(prompts):
            result = ""
            system_message = systems[i] if i < len(systems) else ""
            if system_message:
                result += f"system\n{system_message}\n"
            result += f"user\n{prompt}\nassistant\n"
            results.append(result)
        return results

    elif mode == "codeqwen":
        results = []
        systems = systems or [""] * len(
            prompts
        )  # Default to empty strings if systems is None or shorter than prompts

        for i, prompt in enumerate(prompts):
            result = ""
            system_message = systems[i] if i < len(systems) else ""
            if system_message:
                result += f"system\n{system_message}\n"
            result += f"user\n{prompt}\nassistant\n"
            results.append(result)
        return results

    elif mode == "deepseekcoder":
        results = []
        systems = systems or [""] * len(
            prompts
        )  # Default to empty strings if systems is None or shorter than prompts

        for i, prompt in enumerate(prompts):
            result = ""
            system_message = systems[i] if i < len(systems) else ""
            if system_message:
                result += f"{system_message}\n"
            result += f"### Instruction:\n{prompt}\n### Response:\n"
            results.append(result)
        return results

    elif mode == "artigenz":
        results = []
        systems = systems or [""] * len(
            prompts
        )  # Default to empty strings if systems is None or shorter than prompts

        for i, prompt in enumerate(prompts):
            result = ""
            system_message = systems[i] if i < len(systems) else ""
            if system_message:
                result += f"{system_message}\n"
            result += f"### Instruction:\n{prompt}\n### Response:\n"
            results.append(result)
        return results


def inferSystemModelVllm(
    model,
    prompts,
    system_prompts="Act as a Mario in Super Mario Brothers",
    mode="llama3",
    temperature=0.0,
    top_p=1.0,
    max_tokens=2000,
):
    if not isinstance(system_prompts, list):
        system_prompts = [system_prompts] * len(prompts)

    from vllm import LLM, SamplingParams

    if len(system_prompts) != len(prompts):
        raise ValueError(
            "The length of system_prompts must match the length of prompts."
        )

    sampling_params = SamplingParams(
        temperature=temperature, top_p=top_p, max_tokens=max_tokens
    )

    llm = LLM(
        model=f"../text-generation-webui/models/{model}",
        dtype="half",
        max_model_len=8192,
    )
    prompts_with_systems = template(prompts, system_prompts, mode)

    outputs = llm.generate(prompts_with_systems, sampling_params)

    res = []
    for output in outputs:
        prompt = output.prompt
        generated_text = output.outputs[0].text
        res.append(generated_text)

    return res


def inferModelVllm(model, prompts, temperature=0.0, top_p=0.9, max_tokens=2000):
    from vllm import LLM, SamplingParams

    sampling_params = SamplingParams(
        temperature=temperature, top_p=top_p, max_tokens=max_tokens
    )

    llm = LLM(
        model=f"../text-generation-webui/models/{model}",
        dtype="half",
        max_model_len=8192,
    )
    outputs = llm.generate(prompts, sampling_params)

    res = []
    for output in outputs:
        prompt = output.prompt
        generated_text = output.outputs[0].text

        print(generated_text)
        res.append(generated_text)

    return res


def inferModel(
    prompt="This is a cake recipe:\n\n", port=5000, temperature=0.8, max_tokens=200
):
    url = f"http://127.0.0.1:{port}/v1/completions"
    headers = {"Content-Type": "application/json"}

    data = {
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.9,
        "seed": 10,
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        try:
            return response.json()["choices"][0]["text"]
        except:
            return "FAILED TO PARSE RESPONSE"
    else:
        return response.text


def inferSystemModel(
    prompt="This is a cake recipe:\n\n",
    system_prompt="You are a helpful assistant.",
    port=5000,
    temperature=0.8,
    max_tokens=200,
):
    url = f"http://127.0.0.1:{port}/v1/chat/completions"
    headers = {"Content-Type": "application/json"}

    data = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.9,
        "seed": 10,
        "mode": "instruct",
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        try:
            return response.json()["choices"][0]["message"]["content"]
        except:
            return "FAILED TO PARSE RESPONSE"
    else:
        return response.text


def extract_cwe(possible_options, cwe25):
    for cwe in cwe25:
        for possible_id in possible_options:
            possible_id = possible_id[4:]

            if possible_id == cwe["id"]:
                return cwe["id"], cwe["name"], cwe["description"]

    return "", "", ""
