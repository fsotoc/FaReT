#! /usr/bin/env python
#
def beta_values ( n_data ):

#*****************************************************************************80
#
## BETA_VALUES returns some values of the Beta function.
#
#  Discussion:
#
#    Beta(X,Y) = ( Gamma(X) * Gamma(Y) ) / Gamma(X+Y)
#
#    Both X and Y must be greater than 0.
#
#    In Mathematica, the function can be evaluated by:
#
#      Beta[X,Y]
#
#  Properties:
#
#    Beta(X,Y) = Beta(Y,X).
#    Beta(X,Y) = Integral ( 0 <= T <= 1 ) T^(X-1) (1-T)^(Y-1) dT.
#    Beta(X,Y) = Gamma(X) * Gamma(Y) / Gamma(X+Y)
#
#  Licensing:
#
#    This code is distributed under the GNU LGPL license.
#
#  Modified:
#
#    01 January 2015
#
#  Author:
#
#    John Burkardt
#
#  Reference:
#
#    Milton Abramowitz and Irene Stegun,
#    Handbook of Mathematical Functions,
#    US Department of Commerce, 1964.
#
#    Stephen Wolfram,
#    The Mathematica Book,
#    Fourth Edition,
#    Wolfram Media / Cambridge University Press, 1999.
#
#  Parameters:
#
#    Input/output, integer N_DATA.  The user sets N_DATA to 0 before the
#    first call.  On each call, the routine increments N_DATA by 1, and
#    returns the corresponding data; when there is no more data, the
#    output value of N_DATA will be 0 again.
#
#    Output, real X, Y, the arguments of the function.
#
#    Output, real F, the value of the function.
#
  import numpy as np

  n_max = 17

  f_vec = np.array ( ( \
     0.5000000000000000E+01, \
     0.2500000000000000E+01, \
     0.1666666666666667E+01, \
     0.1250000000000000E+01, \
     0.5000000000000000E+01, \
     0.2500000000000000E+01, \
     0.1000000000000000E+01, \
     0.1666666666666667E+00, \
     0.3333333333333333E-01, \
     0.7142857142857143E-02, \
     0.1587301587301587E-02, \
     0.2380952380952381E-01, \
     0.5952380952380952E-02, \
     0.1984126984126984E-02, \
     0.7936507936507937E-03, \
     0.3607503607503608E-03, \
     0.8325008325008325E-04 ) )

  x_vec = np.array ( ( \
     0.2E+00, \
     0.4E+00, \
     0.6E+00, \
     0.8E+00, \
     1.0E+00, \
     1.0E+00, \
     1.0E+00, \
     2.0E+00, \
     3.0E+00, \
     4.0E+00, \
     5.0E+00, \
     6.0E+00, \
     6.0E+00, \
     6.0E+00, \
     6.0E+00, \
     6.0E+00, \
     7.0E+00  ) )

  y_vec = np.array ( ( \
     1.0E+00, \
     1.0E+00, \
     1.0E+00, \
     1.0E+00, \
     0.2E+00, \
     0.4E+00, \
     1.0E+00, \
     2.0E+00, \
     3.0E+00, \
     4.0E+00, \
     5.0E+00, \
     2.0E+00, \
     3.0E+00, \
     4.0E+00, \
     5.0E+00, \
     6.0E+00, \
     7.0E+00  ) )

  if ( n_data < 0 ):
    n_data = 0

  if ( n_max <= n_data ):
    n_data = 0
    x = 0.0
    y = 0.0
    f = 0.0
  else:
    x = x_vec[n_data]
    y = y_vec[n_data]
    f = f_vec[n_data]
    n_data = n_data + 1

  return n_data, x, y, f

def beta_values_test ( ):

#*****************************************************************************80
#
## BETA_VALUES_TEST demonstrates the use of BETA_VALUES.
#
#  Licensing:
#
#    This code is distributed under the GNU LGPL license.
#
#  Modified:
#
#    24 December 2014
#
#  Author:
#
#    John Burkardt
#
  import platform

  print ( '' )
  print ( 'BETA_VALUES_TEST:' )
  print ( '  Python version: %s' % ( platform.python_version ( ) ) )
  print ( '  BETA_VALUES stores values of the BETA function.' )
  print ( '' )
  print ( '      X         Y         BETA(X,Y)' )
  print ( '' )

  n_data = 0

  while ( True ):

    n_data, x, y, f = beta_values ( n_data )

    if ( n_data == 0 ):
      break

    print ( '  %12f  %12f  %24.16g' % ( x, y, f ) )
#
#  Terminate.
#
  print ( '' )
  print ( 'BETA_VALUES_TEST:' )
  print ( '  Normal end of execution.' )
  return

if ( __name__ == '__main__' ):
  from timestamp import timestamp
  timestamp ( )
  beta_values_test ( )
  timestamp ( )

