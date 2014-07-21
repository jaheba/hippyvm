from testing.test_interpreter import BaseTestInterpreter
import pytest

class TestPyPyBridge(BaseTestInterpreter):

    # ------------------------------------------------------
    # Testing the definitions of new Python modules from PHP
    # ------------------------------------------------------

    def test_embed_py_mod(self):
        output = self.run('''
        $m = embed_py_mod("mymod", "def f(): print('hello')");
        echo($m->f());
        ''')
        assert output[0] == self.space.w_Null # XXX for now

    def test_call_func_int_args(self):
        phspace = self.space
        output = self.run('''
        $m = embed_py_mod("mymod", "def f(x): return x+1");
        echo($m->f(665));
        ''')
        assert phspace.int_w(output[0]) == 666

    def test_call_nonexist(self):
        pytest.skip("broken")
        phspace = self.space
        with pytest.raises(Exception) as excinfo:
            output = self.run('''
            $m = embed_py_mod("mymod", "def f(x): return x+1");
            echo($m->g(665));
            ''')
        assert excinfo.value.message.startswith("No such callable")

    def test_multiple_modules(self):
        phspace = self.space
        output = self.run('''
        $m1 = embed_py_mod("mod1", "def f(x): return x+1");
        $m2 = embed_py_mod("mod2", "def g(x): return x-1");
        echo($m1->f(665));
        echo($m2->g(665));
        ''')
        assert phspace.int_w(output[0]) == 666
        assert phspace.int_w(output[1]) == 664

    def test_modules_intercall(self):
        phspace = self.space
        output = self.run('''
        $m1 = embed_py_mod("mod1", "def f(x): return x+1");
        $m2 = embed_py_mod("mod2", "import mod1\ndef g(x): return mod1.f(x)");
        echo($m2->g(1336));
        ''')
        assert phspace.int_w(output[0]) == 1337

    def test_modules_intercall2(self):
        phspace = self.space
        output = self.run('''
        $m1 = embed_py_mod("mod1", "def f(x): return x+1");
        $m2 = embed_py_mod("mod2", "import mod1\ndef g(x): return mod1.f(x)");
        $m3 = embed_py_mod("mod3", "import mod2\ndef h(x): return mod2.g(x)");
        echo($m3->h(41));
        ''')
        assert phspace.int_w(output[0]) == 42

    def test_fib(self):
        phspace = self.space
        output = self.run('''
        $src = <<<EOD
        def fib(n):
            if n == 0: return 0
            if n == 1: return 1
            return fib(n-1) + fib(n-2)
        EOD;

        $m = embed_py_mod("fib", $src);
        $expects = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144];

        for ($i = 0; $i < count($expects); $i++) {
            assert($m->fib($i) == $expects[$i]);
        }
        ''')

    def test_multitype_args(self):
        phspace = self.space
        output = self.run('''
        $src = <<<EOD
        def cat(s, b, i):
            return "%s-%s-%s" % (s, b, i)
        EOD;

        $m = embed_py_mod("meow", $src);
        echo($m->cat("123", True, 666));
        ''')
        assert phspace.str_w(output[0]) == "123-True-666"

    def test_variadic_args(self):
        phspace = self.space
        output = self.run('''
        $src = <<<EOD
        def cat(*args):
            return "-".join([str(x) for x in args])
        EOD;

        $m = embed_py_mod("meow", $src);
        echo($m->cat(5, 4, 3, 2, 1, "Thunderbirds", "Are", "Go"));
        ''')
        assert phspace.str_w(output[0]) == "5-4-3-2-1-Thunderbirds-Are-Go"

    def test_kwargs_exhaustive(self):
        phspace = self.space
        output = self.run('''
        $src = <<<EOD
        def cat(x="111", y="222", z="333"):
            return "-".join([x, y, z])
        EOD;

        $m = embed_py_mod("meow", $src);
        echo($m->cat("abc", "def", "ghi"));
        ''')
        assert phspace.str_w(output[0]) == "abc-def-ghi"

    def test_kwargs_nonexhaustive(self):
        phspace = self.space
        output = self.run('''
        $src = <<<EOD
        def cat(x="111", y="222", z="333"):
            return "-".join([x, y, z])
        EOD;

        $m = embed_py_mod("meow", $src);
        echo($m->cat("abc", "def"));
        ''')
        assert phspace.str_w(output[0]) == "abc-def-333"

    def test_phbridgeproxy_equality(self):
        phspace = self.space
        output = self.run('''
        $src = <<<EOD
        def cmp(x, y):
            return x == y
        EOD;

        $m = embed_py_mod("cmps", $src);

        class Flibble {
            public $val;
            function __construct($val) {
                $this->val = $val;
            }
        }
        $x = new Flibble("123");
        $y = new Flibble("123");
        echo($m->cmp($x, $y));
        ''')
        assert phspace.is_true(output[0])

    def test_phbridgeproxy_nequality(self):
        phspace = self.space
        output = self.run('''
        $src = <<<EOD
        def cmp(x, y):
            return x == y
        EOD;

        $m = embed_py_mod("cmps", $src);

        class Flibble {
            public $val;
            function __construct($val) {
                $this->val = $val;
            }
        }
        $x = new Flibble("666");
        $y = new Flibble("123");
        echo($m->cmp($x, $y));
        ''')
        assert not phspace.is_true(output[0])

    def test_phbridgeproxy_nequality2(self):
        phspace = self.space
        output = self.run('''
        $src = <<<EOD
        def ncmp(x, y):
            return x != y
        EOD;

        $m = embed_py_mod("cmps", $src);

        class Flibble {
            public $val;
            function __construct($val) {
                $this->val = $val;
            }
        }
        $x = new Flibble("666");
        $y = new Flibble("123");
        echo($m->ncmp($x, $y));
        ''')
        assert phspace.is_true(output[0])

    def test_pystone(self):
        pytest.skip("need to enable time module in pypy")
        output = self.run('''
        $src = <<<EOD
        def mystone():
                from test import pystone
                pystone.main()
        EOD;

        embed_py_func($src);
        mystone();
        ''')
        # just check it runs

    # ------------------------------------------------------
    # Testing calling PHP from Python
    # ------------------------------------------------------

    def test_callback_to_php(self):
        phspace = self.space
        output = self.run('''
        function hello() {
            echo "foobar";
        }

        $src = <<<EOD
        def call_php():
            hello()
        EOD;

        embed_py_func($src);
        call_php();
        ''')
        assert phspace.str_w(output[0]) == "foobar"

    # XXX Test kwargs

    def test_obj_proxy(self):
        phspace = self.space
        output = self.run('''
        $src = <<<EOD
        import sys
        def get():
            return sys
        EOD;
        $m = embed_py_mod("m", $src);
        echo($m->get()->__name__);
        ''')
        assert phspace.str_w(output[0]) == "sys"

    def test_inplace_function(self):
        phspace = self.space
        output = self.run('''
        $src = <<<EOD
        def test():
            return "jibble"
        EOD;
        embed_py_func($src);
        echo(test());
        ''')
        assert phspace.str_w(output[0]) == "jibble"

    def test_inplace_function_args(self):
        phspace = self.space
        output = self.run('''
        $src = <<<EOD
        def cat(x, y, z):
            return "%s-%s-%s" % (x, y, z)
        EOD;
        embed_py_func($src);
        echo(cat("t", "minus", 10));
        ''')
        assert phspace.str_w(output[0]) == "t-minus-10"

    def test_return_function_to_php(self):
        pytest.skip("broken in some bizarre way. calling fdopen!")
        phspace = self.space
        output = self.run('''
$src = <<<EOD
def cwd():
    import os
    return os.getpid
EOD;

embed_py_func($src);

echo "111111\n";
$x = cwd();
echo "222222\n";
echo $x();
echo "333333\n";
        ''')
        import os
        assert phspace.int_w(output[0]) == os.getpid()

    def test_closures_are_intact(self):
        """ Check we didn't break closures """
        phspace = self.space
        output = self.run('''
        $src = <<<EOD
        def mk_get_x(x, y):
            def get_x():
                return x + y
            return get_x
        EOD;
        embed_py_func($src);

        $f = mk_get_x(2, 4);
        echo($f());
        ''')
        assert phspace.int_w(output[0]) == 6

    def test_php2py_cross_lang_closure_is_late_binding(self):
        phspace = self.space
        output = self.run('''
$x = 42;
$src = <<<EOD
def f():
    return x;
EOD;
embed_py_func($src);
$x = 43;

echo(f());
        ''')
        assert phspace.int_w(output[0]) == 43


    def test_php2py_cross_lang_closure_is_late_binding2(self):
        phspace = self.space
        output = self.run('''
$x = 64;
$src = <<<EOD
def f():
    def g():
        return x;
    return g
EOD;
embed_py_func($src);
$x = 11;

$g = f();
echo($g());
        ''')
        assert phspace.int_w(output[0]) == 11


    def test_py2php_cross_lang_closure_is_late_binding(self):
        phspace = self.space
        output = self.run('''
$src = <<<EOD
def f():
    x = 44
    php_src = "function g() { return \$x; }"
    g = embed_php_func(php_src)
    x += 1
    return g()
EOD;
embed_py_func($src);

echo(f());
        ''')
        assert phspace.int_w(output[0]) == 45

    def test_py2php_cross_lang_closure_is_late_binding2(self):
        phspace = self.space
        output = self.run('''
$x = 44;
$src = <<<EOD
def f():
    php_src = "function g() { return \$x; }"
    g = embed_php_func(php_src)
    x = 45
    return g()
EOD;
embed_py_func($src);

echo(f());
        ''')
        assert phspace.int_w(output[0]) == 45