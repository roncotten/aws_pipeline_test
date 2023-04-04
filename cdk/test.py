def my_func(**kwargs):
  print(kwargs)
  print(kwargs.get('foo'))

my_func(foo='bar', bar='foo')
