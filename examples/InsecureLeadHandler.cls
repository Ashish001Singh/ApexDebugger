// SHOWCASE: security gaps — hardcoded ID, no CRUD/FLS, no sharing declaration.
public class InsecureLeadHandler {
    private static final Id SALES_RT_ID = '012000000000AAAAAQ';

    public void assignAndInsert(Lead l) {
        l.RecordTypeId = SALES_RT_ID;
        insert l;
    }
}
