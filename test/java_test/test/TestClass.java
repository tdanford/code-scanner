package test; 

public class TestClass {

    public static void main(String[] args) { 
        TestClass tc = new TestClass(10); 

        System.out.println(tc.getValue()); 
    }

    private int value; 

    public TestClass(final int _value) {
        this.value = _value; 
    }

    public int getValue() {
        return this._value;
    }
}