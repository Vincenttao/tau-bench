package eval;

import java.nio.file.*;

public final class InvocationSequenceTest {
    public static void main(String[] args) throws Exception {
        Path directory=Files.createTempDirectory("hub-invocation-sequence-");
        Path file=directory.resolve("sequence");
        try(var first=new InvocationSequence(file)) {
            if(first.next()!=1 || first.next()!=2) throw new AssertionError("Initial sequence");
            try(var duplicate=new InvocationSequence(file)) {throw new AssertionError("Duplicate writer");}
            catch(IllegalStateException expected) { }
        }
        try(var restarted=new InvocationSequence(file)) {
            if(restarted.next()!=3) throw new AssertionError("Restart reused official invocation identity");
        }
        try(var paths=Files.walk(directory)) {
            for(Path p:paths.sorted(java.util.Comparator.reverseOrder()).toList()) Files.delete(p);
        }
        System.out.println("InvocationSequenceTest: passed");
    }
}
