package uz.agentlar.phone;
final class PairGate {
 private long generation=0;
 synchronized long begin(){return ++generation;}
 synchronized void cancel(){++generation;}
 synchronized boolean current(long value){return generation==value;}
}
