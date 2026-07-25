// SHOWCASE: cross-language risk — this component consumes an Apex controller
// (InsecureLeadHandler) that enforces no CRUD/FLS or sharing. Neither single-file
// review flags the compounded exposure; the correlator does.
import { LightningElement, wire } from 'lwc';
import getLeads from '@salesforce/apex/InsecureLeadHandler.getLeads';

export default class LeadList extends LightningElement {
    @wire(getLeads)
    wiredLeads({ data, error }) {
        if (data) {
            this.leads = data;
        } else if (error) {
            this.error = error;
        }
    }
}
