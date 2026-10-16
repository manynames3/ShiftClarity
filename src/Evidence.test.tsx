import {it,expect} from 'vitest';
import {render,screen} from '@testing-library/react';
import {Evidence,SourceDocument} from './Evidence';
import {initialDemo} from './domain/demo';
import {freshInputs,draftRule} from './adapters/fixtures';

const noop=()=>{};

it('item 7: evidence reports loading, unavailable and refresh-error states',()=>{
 const state=initialDemo(freshInputs(),draftRule);state.run=null;
 const view=render(<Evidence state={state} finding={undefined} onAction={noop} onExport={noop} loading/>);
 expect(screen.getByRole('status')).toHaveTextContent('Loading linked evidence');
 view.rerender(<Evidence state={state} finding={undefined} onAction={noop} onExport={noop} error="Source service unavailable."/>);
 expect(screen.getByRole('alert')).toHaveTextContent('Source service unavailable.');
 view.rerender(<Evidence state={initialDemo(freshInputs(),draftRule)} finding={undefined} onAction={noop} onExport={noop}/>);
 expect(screen.getByRole('status')).toHaveTextContent('Finding is outside the current run');
});

it('item 7: an unregistered agreement excerpt is shown as an evidence error',()=>{
 const inputs=freshInputs(),rule={...inputs.rules[0],source_excerpt_id:'EX-MISSING'};
 render(<SourceDocument inputs={inputs} rule={rule}/>);
 expect(screen.getByRole('alert')).toHaveTextContent('Source excerpt unavailable');
});
