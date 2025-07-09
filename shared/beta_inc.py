#! /usr/bin/env python
#
def beta_inc ( a, b, x ):

#*****************************************************************************80
#
## BETA_INC returns the value of the incomplete Beta function.
#
#  Discussion:
#
#    This calculation requires an iteration.  In some cases, the iteration
#    may not converge rapidly, or may become inaccurate.
#
#    BETA_INC(A,B,X)
#
#      =   Integral ( 0 <= T <= X ) T^(A-1) (1-T)^(B-1) dT
#        / Integral ( 0 <= T <= 1 ) T^(A-1) (1-T)^(B-1) dT
#
#      =   Integral ( 0 <= T <= X ) T^(A-1) (1-T)^(B-1) dT
#        / BETA(A,B)
#
#  Licensing:
#
#    This code is distributed under the GNU LGPL license.
#
#  Modified:
#
#    05 March 2016
#
#  Author:
#
#    Original FORTRAN77 version by Majumder, Bhattacharjee.
#    Python version by John Burkardt.
#
#  Reference:
#
#    Majumder and Bhattacharjee,
#    Algorithm AS63,
#    Applied Statistics,
#    1973, volume 22, number 3.
#
#  Parameters:
#
#    Input, A, B, the parameters of the function.
#    0.0D+00 < A,
#    0.0D+00 < B.
#
#    Input, real X, the argument of the function.
#    Normally, 0.0 <= X <= 1.0.
#
#    Output, BETA_INC, the value of the function.
#
  import numpy as np
  from r8_beta import r8_beta
  from sys import exit

  it_max = 1000
  tol = 1.0E-07

  if ( a <= 0.0 ):
    print ( '' )
    print ( 'BETA_INC - Fatal error!' )
    print ( '  A <= 0.' )
    exit ( 'BETA_INC - Fatal error!' )

  if ( b <= 0.0 ):
    print ( '' )
    print ( 'BETA_INC - Fatal error!' )
    print ( '  B <= 0.' )
    exit ( 'BETA_INC - Fatal error!' )

  if ( x <= 0.0 ):
    value = 0.0
    return value
  elif ( 1.0 <= x ):
    value = 1.0
    return value
#
#  Change tail if necessary and determine S.
#
  psq = a + b

  if ( a < ( a + b ) * x ):
    xx = 1.0 - x
    cx = x
    pp = b
    qq = a
    indx = 1
  else:
    xx = x
    cx = 1.0 - x
    pp = a
    qq = b
    indx = 0

  term = 1.0
  i = 1
  value = 1.0

  ns = np.floor ( qq + cx * ( a + b ) )
#
#  Use Soper's reduction formulas.
#
  rx = xx / cx

  temp = qq - i
  if ( ns == 0 ):
    rx = xx

  it = 0

  while ( True ):

    it = it + 1

    if ( it_max < it ):
      print ( '' )
      print ( 'BETA_INC - Fatal error!' )
      print ( '  Maximum number of iterations exceeded!' )
      print ( '  IT_MAX = %d' % ( it_max ) )
      exit ( 'BETA_INC - Fatal error!' )

    term = term * temp * rx / ( pp + i )
    value = value + term
    temp = abs ( term )

    if ( temp <= tol and temp <= tol * value ):
      break

    i = i + 1
    ns = ns - 1

    if ( 0 <= ns ):
      temp = qq - i
      if ( ns == 0 ):
        rx = xx
    else:
      temp = psq
      psq = psq + 1.0
#
#  Finish calculation.
#
  value = value * np.exp ( pp * np.log ( xx ) \
    + ( qq - 1.0 ) * np.log ( cx ) ) \
    / ( r8_beta ( a, b ) * pp )

  if ( indx ):
    value = 1.0 - value

  return value

def beta_inc_test ( ):

#*****************************************************************************80
#
## BETA_INC_TEST tests BETA_INC.
#
#  Licensing:
#
#    This code is distributed under the GNU LGPL license.
#
#  Modified:
#
#    05 March 2016
#
#  Author:
#
#    John Burkardt
#
  import platform
  from beta_inc_values import beta_inc_values

  print ( '' )
  print ( 'BETA_INC_TEST:' )
  print ( '  Python version: %s' % ( platform.python_version ( ) ) )
  print ( '  BETA_INC evaluates the normalized incomplete Beta' )
  print ( '  function BETA_INC(A,B,X).' )
  print ( '' )
  print ( '      A           B           X               Exact F     BETA_INC(A,B,X)' )
  print ( '' )

  n_data = 0

  while ( True ):

    n_data, a, b, x, fx = beta_inc_values ( n_data )

    if ( n_data == 0 ):
      break

    fx2 = beta_inc ( a, b, x )

    print ( '  %10g  %10g  %10g  %14g  %14g' % ( a, b, x, fx, fx2 ) )
#
#  Terminate.
#
  print ( '' )
  print ( 'BETA_INC_TEST' )
  print ( '  Normal end of execution.' )
  return

if ( __name__ == '__main__' ):
  from timestamp import timestamp
  timestamp ( )
  beta_inc_test ( )
  timestamp ( )

