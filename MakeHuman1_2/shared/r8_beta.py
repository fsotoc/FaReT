#! /usr/bin/env python
#
def r8_beta ( a, b ):

#*****************************************************************************80
#
## R8_BETA returns the value of the Beta function.
#
#  Discussion:
#
#    BETA(A,B) = ( GAMMA ( A ) * GAMMA ( B ) ) / GAMMA ( A + B )
#              = Integral ( 0 <= T <= 1 ) T^(A-1) (1-T)^(B-1) dT.
#
#  Licensing:
#
#    This code is distributed under the GNU LGPL license.
#
#  Modified:
#
#    02 September 2004
#
#  Author:
#
#    John Burkardt
#
#  Parameters:
#
#    Input, real A, B, the parameters of the function.
#    0.0D+00 < A,
#    0.0D+00 < B.
#
#    Output, real R8_BETA, the value of the function.
#
  import numpy as np
  from r8_gamma import r8_gamma
  from sys import exit

  if ( a <= 0.0 or b <= 0.0 ):
    print ( '' )
    print ( 'R8_BETA - Fatal error!' )
    print ( '  Both A and B must be greater than 0.' )
    exit ( 'R8_BETA - Fatal error!' )

  value = r8_gamma ( a ) * r8_gamma ( b ) / r8_gamma ( a + b )

  return value

def r8_beta_test ( ):

#*****************************************************************************80
#
## R8_BETA_TEST tests R8_BETA.
#
#  Licensing:
#
#    This code is distributed under the GNU LGPL license.
#
#  Modified:
#
#    03 March 2016
#
#  Author:
#
#    John Burkardt
#
  import platform
  from beta_values import beta_values

  print ( '' )
  print ( 'R8_BETA_TEST:' )
  print ( '  Python version: %s' % ( platform.python_version ( ) ) )
  print ( '  R8_BETA evaluates the BETA function.' )
  print ( '' )
  print ( '      X         Y         BETA(X,Y)         R8_BETA(X,Y)' )
  print ( '                          tabulated         computed.' )
  print ( '' )

  n_data = 0

  while ( True ):

    n_data, x, y, f1 = beta_values ( n_data )

    if ( n_data == 0 ):
      break

    f2 = r8_beta ( x, y )

    print ( '  %12g  %12g  %24.16g  %24.16g' % ( x, y, f1, f2 ) )
#
#  Terminate.
#
  print ( '' )
  print ( 'R8_BETA_TEST:' )
  print ( '  Normal end of execution.' )
  return

if ( __name__ == '__main__' ):
  from timestamp import timestamp
  timestamp ( )
  r8_beta_test ( )
  timestamp ( )
