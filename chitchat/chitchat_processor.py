# coding: utf-8
'''模型及代码改装自[CDial-GPT](https://github.com/thu-coai/CDial-GPT)'''


from typing import Any, Dict, List

import torch
from transformers import GPT2LMHeadModel, BertTokenizer

from ..processor import ProcessorBase


class ChitchatProcessor(ProcessorBase):
    def _load(self, conf: Dict[str, Any]) -> None:
        chkpt = self.get_resource_path(conf['model_chkpt'])
        self.tokenizer = BertTokenizer.from_pretrained(chkpt, do_lower_case=True)
        self.model = GPT2LMHeadModel.from_pretrained(chkpt).eval()

        self.greedy = conf.get('greedy', False)
        self.max_out_len = conf.get('max_out_len', 30)
        self.min_out_len = conf.get('min_out_len', 1)
        self.temperature = conf.get('temperature', 0.7)
        self.top_k = conf.get('top_k', 0)
        self.top_p = conf.get('top_p', 0.9)

        # special tokens
        special_tokens = ['[CLS]', '[SEP]', '[PAD]', '[speaker1]', '[speaker2]']
        self.special_tokens_ids = self.tokenizer.convert_tokens_to_ids(special_tokens)
        self.id_bos, self.id_eos, self.id_pad, self.id_speaker1, self.id_speaker2 = self.special_tokens_ids

    def _tokenize(self, utterance: str) -> List[int]:
        # XXX 验一下需不需要这一行
        # utterance = ' '.join(utterance.replace(' ', ''))
        return self.tokenizer.convert_tokens_to_ids(self.tokenizer.tokenize(utterance))

    def preprocess(self, params: Dict[str, Any]) -> Dict[str, Any]:
        params['utterance'] = self._tokenize(params['utterance'])
        params['history'] = [self._tokenize(s) for s in params.get('history', [])]
        return params

    @torch.no_grad()
    def model_process(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'resp': self._sample_sequence(params['utterance'], params['history'])
        }

    def postprocess(self, params: Dict[str, Any], model_res: Dict[str, Any]) -> Dict[str, Any]:
        resp = self.tokenizer.decode(model_res['resp'], skip_special_tokens=True)
        return {
            'resp': resp.replace(' ', '')
        }

    def _sample_sequence(self, utterance: List[int], history: List[List[int]] = None) -> List[int]:
        '''抽样生成回复
        TODO beam search
        '''
        ret = []
        input = self._init_input(utterance, history)
        persona = input['token_type_ids'][-1]
        for i in range(self.max_out_len):
            # set model input, and batch_size = 1
            input_ids = torch.tensor(input['input_ids'], dtype=torch.long).unsqueeze(0)
            token_type_ids = torch.tensor(input['token_type_ids'], dtype=torch.long).unsqueeze(0)
            # forward
            logits, *_ = self.model(input_ids, token_type_ids=token_type_ids)
            # filter logits
            logits = logits[0, -1, :] / self.temperature
            logits = self._top_filtering(logits, top_k=self.top_k, top_p=self.top_p)
            # sample
            probs = torch.nn.Softmax(dim=-1)(logits)
            id = torch.topk(probs, 1)[1] if self.greedy else torch.multinomial(probs, 1)
            if i < self.min_out_len and id.item() in self.special_tokens_ids:
                while id.item() in self.special_tokens_ids:
                    id = torch.multinomial(probs, num_samples=1)
            if id.item() in self.special_tokens_ids:
                break
            ret.append(id.item())
            # update input
            input['input_ids'].append(id.item())
            input['token_type_ids'].append(persona)

        return ret

    def _init_input(self, utterance: List[int], history: List[List[int]] = None) -> Dict[str, List[int]]:
        '''![表示方式](https://github.com/thu-coai/CDial-GPT/raw/master/figures/inputs.png)'''
        input_ids = [self.id_bos]
        token_type_ids = [self.id_bos]
        seq = history + [utterance, []]
        for i, s in enumerate(seq):
            persona = self.id_speaker1 if i % 2 == 0 else self.id_speaker2
            input_ids.extend([persona] + s)
            token_type_ids.extend([persona] * (len(s) + 1))
        return {
            'input_ids': input_ids,
            'token_type_ids': token_type_ids,
        }

    def _top_filtering(self, logits, top_k=0, top_p=0.0, threshold=-float('Inf'), filter_value=-float('Inf')):
        """ Filter a distribution of logits using top-k, top-p (nucleus) and/or threshold filtering
            Args:
                logits: logits distribution shape (vocabulary size)
                top_k: <=0: no filtering, >0: keep only top k tokens with highest probability.
                top_p: <=0.0: no filtering, >0.0: keep only a subset S of candidates, where S is the smallest subset
                    whose total probability mass is greater than or equal to the threshold top_p.
                    In practice, we select the highest probability tokens whose cumulative probability mass exceeds
                    the threshold top_p.
                threshold: a minimal threshold to keep logits
        """
        assert logits.dim() == 1  # Only work for batch size 1 for now - could update but it would obfuscate a bit the code
        if top_k > 0:
            # Remove all tokens with a probability less than the last token in the top-k tokens
            top_k = min(top_k, logits.size(-1))
            indices_to_remove = logits < torch.topk(logits, top_k)[0][..., -1, None]
            logits[indices_to_remove] = filter_value

        if top_p > 0.0:
            # Compute cumulative probabilities of sorted tokens
            sorted_logits, sorted_indices = torch.sort(logits, descending=True)
            cumulative_probabilities = torch.cumsum(torch.nn.Softmax(dim=-1)(sorted_logits), dim=-1)

            # Remove tokens with cumulative probability above the threshold
            sorted_indices_to_remove = cumulative_probabilities > top_p
            # Shift the indices to the right to keep also the first token above the threshold
            sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
            sorted_indices_to_remove[..., 0] = 0

            # Back to unsorted indices and set them to -infinity
            indices_to_remove = sorted_indices[sorted_indices_to_remove]
            logits[indices_to_remove] = filter_value

        indices_to_remove = logits < threshold
        logits[indices_to_remove] = filter_value

        return logits
