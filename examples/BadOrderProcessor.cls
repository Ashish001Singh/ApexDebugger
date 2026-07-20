// SHOWCASE: governor-limit + performance offender. Run:
//   PYTHONPATH=. uv run copilot review examples/BadOrderProcessor.cls
public class BadOrderProcessor {
    public void processOrders(List<Id> accountIds) {
        for (Id accId : accountIds) {
            List<Order__c> orders = [SELECT Id, Status__c FROM Order__c WHERE Account__c = :accId];
            for (Order__c o : orders) {
                for (Integer i = 0; i < 3; i++) {
                    o.Retry_Count__c = i;
                }
                o.Status__c = 'Processed';
                update o;
            }
        }
    }
}
