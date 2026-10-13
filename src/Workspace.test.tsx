import {it,expect} from 'vitest';
import {render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {Workspace} from './Workspace';
import {freshInputs} from './adapters/fixtures';
import {reconcile} from './domain/engine';
it('SC-02,19: filtering changes visible findings while preserving coverage',async()=>{const user=userEvent.setup();render(<Workspace run={reconcile(freshInputs())} reviews={{}}/>);expect(screen.getByText('12 of 14 shifts rule-checked')).toBeInTheDocument();await user.type(screen.getByRole('textbox',{name:'Search findings'}),'no such finding');expect(screen.getByText('No findings match these filters')).toBeInTheDocument();expect(screen.getByText('12 of 14 shifts rule-checked')).toBeInTheDocument();await user.click(screen.getByRole('button',{name:'Clear filters'}));expect(screen.getByText('Rate change not reflected')).toBeInTheDocument();});
it('own-data extension: facility filters derive from loaded records',async()=>{const i=freshInputs();i.work=i.work.filter(w=>w.facility_id==='FAC-001');i.invoices=i.invoices.filter(l=>l.facility_id==='FAC-001');const user=userEvent.setup();render(<Workspace run={reconcile(i)} reviews={{}}/>);expect(screen.getByRole('option',{name:'Pinehaven Care Center'})).toBeInTheDocument();expect(screen.queryByRole('option',{name:'Willowbend Medical Pavilion'})).not.toBeInTheDocument();await user.selectOptions(screen.getByLabelText('Facility'),'FAC-001');expect(screen.getByText('Rate change not reflected')).toBeInTheDocument();});
