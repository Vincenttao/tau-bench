"""Six synthetic probes only. Never invokes benchmark tools or opens Hub writes."""
import argparse
import base64
import getpass
import hashlib
import io
import json
import os
from pathlib import Path
import time
import uuid

from jev_provider import JevClient, JevError, MODEL, claim_request, interpret_claim, visible_box


def fixtures():
    text = [
        ('text_supported', 'The Harbor card has no annual fee. Its foreign transaction fee is waived for premium subscribers.', 'Premium subscribers pay no foreign transaction fee on the Harbor card.', 'supported'),
        ('text_unsupported', 'The Harbor card has no annual fee. Its foreign transaction fee is 3% for every customer.', 'Premium subscribers pay no foreign transaction fee on the Harbor card.', 'unsupported'),
        ('text_missing', 'The bank branch opens at 9 AM.', 'Premium subscribers pay no foreign transaction fee on the Harbor card.', 'unknown'),
        ('text_chinese', '港湾卡免年费。高级订阅客户免收该卡的外币交易手续费。', '高级订阅客户使用港湾卡不收外币交易手续费。', 'supported')]
    result = [(name, claim_request(evidence, claim), expected) for name, evidence, claim, expected in text]
    from PIL import Image, ImageDraw
    for present in (True, False):
        image = Image.new('RGB', (640, 480), 'white')
        draw = ImageDraw.Draw(image)
        draw.rectangle((160,120,479,359), fill='red' if present else 'blue')
        stream = io.BytesIO();image.save(stream, format='PNG')
        ref = str(uuid.uuid4())
        request = {'model': MODEL, 'state': {'photo': ref},
                   'assets': {ref: {'type': 'image', 'format': 'png', 'data_base64': base64.b64encode(stream.getvalue()).decode()}},
                   'questions': {'present': {'type': 'noul', 'instructions': 'Is there a red rectangle in `photo`?'},
                                 'target': {'type': 'box', 'instructions': 'The red rectangle in `photo`.'}}}
        result.append(('image_present' if present else 'image_absent', request, present))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--model', choices=[MODEL, 'jev-latest', 'jev-preview'], default=MODEL)
    args = parser.parse_args()
    cases = fixtures()
    for _, request, _ in cases:
        request['model'] = args.model
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = {'scope':'synthetic provider probes; not Hub integration or benchmark', 'model':args.model,'version_pinned':args.model == MODEL,
                'max_inference_requests':6,'budget_usd':0.50,'reserve_usd_per_request':0.01,
                'input_usd_per_million':0.042,'price_source':'https://docs.typesafe.ai/models',
                'price_checked_date':'2026-11-17','automatic_retries':0,'long_context':False,
                'billing_note':'Public list-price estimate, not account billing; one standard-context request reserved before send.',
                'source_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path(__file__).with_name('jev_provider.py')]}}
    (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    for name,request,expected in cases:
        (args.output/(name+'-request.json')).write_text(json.dumps(request,ensure_ascii=False,indent=2)+'\n')
    if not args.execute:
        print('Prepared 6 synthetic requests; no API calls.');return
    key = os.environ.get('TYPESAFE_API_KEY') or getpass.getpass('TypeSafe key (not saved): ')
    client = JevClient(key); del key
    records=[];spent=0.0
    try:
        models=client.models()
        (args.output/'models.json').write_text(json.dumps(models,indent=2)+'\n')
        if args.model not in [m.get('name') for m in models.get('models',[])]:
            raise JevError('Pinned model is not listed for this account')
        for name,request,expected in cases:
            if spent + 0.01 > 0.50: raise JevError('Budget reservation refused')
            started=time.monotonic()
            record={'case':name,'expected':expected,'status':'attempted'}
            records.append(record)
            # Persist attempt before sending; interruptions must not silently repeat it.
            (args.output/'summary.json').write_text(json.dumps(records,indent=2)+'\n')
            try:
                response=client.ask(request)
                (args.output/(name+'-response.json')).write_text(json.dumps(response,ensure_ascii=False,indent=2)+'\n')
                record.update(actual_model=response['model'],usage=response['usage'])
                spent += response['usage']['input_tokens'] * 0.042 / 1_000_000
                if args.model == MODEL and response['model'] != MODEL: raise JevError('Pinned model identity mismatch')
                if name.startswith('text'):
                    actual=interpret_claim(response);passed=actual==expected
                else:
                    actual=visible_box(response);passed=(actual is not None)==expected
                    if expected and actual:
                        passed = passed and all(abs(actual[k]-v)<=0.1 for k,v in {'left':0.25,'right':0.75,'top':0.25,'bottom':0.75}.items())
                record.update(status='answered',actual=actual,probe_pass=passed)
            except JevError as error:
                record.update(status='error',error=str(error))
                raise
            finally:
                record.update(elapsed_seconds=round(time.monotonic()-started,3),cumulative_estimated_usd=spent)
                (args.output/'summary.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
                print(json.dumps(record,ensure_ascii=False),flush=True)
    except JevError as error:
        (args.output/'error.json').write_text(json.dumps({'error':str(error),'automatic_retry':False})+'\n')
        print('Stopped:',error,flush=True)
        raise SystemExit(1)


if __name__=='__main__':main()
