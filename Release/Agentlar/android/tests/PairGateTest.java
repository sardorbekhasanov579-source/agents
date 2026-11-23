package uz.agentlar.phone;
public class PairGateTest {
 public static void main(String[] args){PairGate g=new PairGate();long pending=g.begin();g.cancel();if(g.current(pending))throw new AssertionError("Stop must cancel pair");long newer=g.begin();if(g.current(pending)||!g.current(newer))throw new AssertionError("Only latest pairing allowed");System.out.println("PairGate tests passed");}
}
