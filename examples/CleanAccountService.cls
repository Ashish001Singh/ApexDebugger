// SHOWCASE: what good looks like — bulkified, secured, sharing-explicit.
public with sharing class CleanAccountService {
    public void tagActiveAccounts(List<Id> accountIds) {
        List<Account> accounts = [
            SELECT Id, Status__c FROM Account
            WHERE Id IN :accountIds WITH USER_MODE
        ];
        List<Account> toUpdate = new List<Account>();
        for (Account a : accounts) {
            a.Status__c = 'Active';
            toUpdate.add(a);
        }
        if (!toUpdate.isEmpty()) {
            try {
                update toUpdate as user;
            } catch (DmlException e) {
                throw new AuraHandledException('Account update failed: ' + e.getMessage());
            }
        }
    }
}
